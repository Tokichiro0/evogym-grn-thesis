import os
import sys
import numpy as np
from pathlib import Path
import shutil
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from algorithms.experiment import Experiment
from algorithms.EA_classes import Individual
from algorithms.GRN_2D import GRN, initialization, mutation_type1, unequal_crossover_prop
from simulation.simulation_resources import simulate_evogym_batch
from simulation.prepare_robot_files import prepare_robot_files
from utils.metrics import genopheno_abs_metrics, behavior_abs_metrics, relative_metrics
from utils.config import Config

def _is_simulatable(ind):
    if not ind.valid:
        return False
    if ind.num_voxels < 2:
        return False
    return True  #evogym_structure check verwijderd

class EA(Experiment):
    def __init__(self, args=None):
        self.args = Config()._get_params()
        super().__init__(self.args)

        self.MAX_GENOME_SIZE = 1000
        self.INI_GENOME_SIZE = 300
        self.PROMOTOR_THRESHOLD = 0.95
        self.novelty_archive = []
        self.archive_add_frac = 0.05
        self.cube_face_size = self.args.cube_face_size
        self.max_voxels = self.args.max_voxels
        self.voxel_types = self.args.voxel_types
        self.plastic = self.args.plastic
        self.env_conditions = self.args.env_conditions
        self.population_size = self.args.population_size
        self.offspring_size = self.args.offspring_size
        self.crossover_prob = self.args.crossover_prob
        self.mutation_prob = self.args.mutation_prob
        self.tournament_k = self.args.tournament_k
        self.num_generations = self.args.num_generations
        self.fitness_metric = self.args.fitness_metric
        self.elitism = getattr(self.args, "elitism", 3)
        self.ustatic = self.args.ustatic
        self.udynamic = self.args.udynamic
        self.min_voxels = int(getattr(self.args, "min_voxels", max(6, round(0.25 * int(self.max_voxels)))))
        self.target_voxels = int(getattr(self.args, "target_voxels", max(self.min_voxels, round(0.65 * int(self.max_voxels)))))
        self.min_actuators = int(getattr(self.args, "min_actuators", max(2, round(0.18 * self.target_voxels))))
        self.min_material_types = int(getattr(self.args, "min_material_types", 3))
        self.size_weight = float(getattr(self.args, "size_weight", 0.25))
        self.complexity_weight = float(getattr(self.args, "complexity_weight", 0.20))
        self.actuator_weight = float(getattr(self.args, "actuator_weight", 0.20))
        self.move_epsilon = float(getattr(self.args, "move_epsilon", 1e-3))
        self.immobile_factor = float(getattr(self.args, "immobile_factor", 0.10))

    def develop_phenotype(self, genome, voxel_types):
        phenotype = GRN(
            promoter_threshold=self.PROMOTOR_THRESHOLD,
            max_voxels=self.max_voxels,
            cube_face_size=self.cube_face_size,
            voxel_types=voxel_types,
            genotype=genome,
            env_conditions=self.env_conditions,
            plastic=self.plastic,
        ).develop()

        phenotype_materials = np.zeros(phenotype.shape, dtype=int)
        phase_grid = np.zeros(phenotype.shape, dtype=float)

        for index, value in np.ndenumerate(phenotype):
            if value != 0:
                phenotype_materials[index] = value.voxel_type
                phase_grid[index] = value.phase
            else:
                phenotype_materials[index] = 0
                phase_grid[index] = 0.0
        return phenotype_materials, phase_grid

    def initialize_population(self, size, generation):
        individuals = []
        for _ in range(size):
            self.id_counter += 1
            ind = Individual(initialization(self.rng, self.INI_GENOME_SIZE), self.id_counter,
                             parent1_id=None, parent2_id=None)
            ind.born_generation = generation
            individuals.append(ind)
        return individuals

    def _phase_mask(self, phase_grid):
        return phase_grid > 0.0
    def _inherit_phase_grid(self, child, parent1, parent2):
        if not hasattr(parent1, "phase_grid") or not hasattr(parent2, "phase_grid"):
            return
        if parent1.phase_grid is None or parent2.phase_grid is None:
            return
        if parent1.phase_grid.shape != parent2.phase_grid.shape:
            return

        mask = np.array([
            [self.rng.random() < 0.5 for _ in range(parent1.phase_grid.shape[1])]
            for _ in range(parent1.phase_grid.shape[0])
        ])
        child.phase_grid = np.where(mask, parent1.phase_grid, parent2.phase_grid)

    def _mutate_phase_grid(self, individual, sigma=0.35, cell_prob=0.25):
        if not hasattr(individual, "phase_grid"):
            return
        if individual.phase_grid is None:
            return

        phase_grid = individual.phase_grid.copy()
        valid_mask = self._phase_mask(phase_grid)

        for i in range(phase_grid.shape[0]):
            for j in range(phase_grid.shape[1]):
                if valid_mask[i, j] and self.rng.random() < cell_prob:
                    phase_grid[i, j] = (phase_grid[i, j] + self.rng.gauss(0, sigma)) % (2 * np.pi)

        individual.phase_grid = phase_grid

    def mutate(self, individual):
        if self.rng.uniform(0, 1) <= self.mutation_prob:
            individual.genome = mutation_type1(self.rng, individual.genome)

        #tijdelijk uitgeschakeld:
        # if self.rng.uniform(0, 1) < 0.25:
        #     self._mutate_phase_grid(individual)

    def crossover(self, parent1, parent2):
        if self.rng.uniform(0, 1) <= self.crossover_prob:
            child_genome = unequal_crossover_prop(
                self.rng,
                self.PROMOTOR_THRESHOLD,
                self.MAX_GENOME_SIZE,
                parent1,
                parent2,
            )
        else:
            chosen = self.rng.choice((parent1, parent2))
            child_genome = list(chosen.genome)
        self.id_counter += 1
        child = Individual(child_genome, self.id_counter, parent1_id=parent1.id, parent2_id=parent2.id)
        return child

    def _morphology_stats(self, ind):
        body = np.asarray(getattr(ind, "phenotype", np.zeros((0, 0))), dtype=int)
        if body.size == 0:
            return {
                "voxels": 0, "h_actuators": 0, "v_actuators": 0,
                "actuators": 0, "material_types": 0, "width": 0,
                "height": 0, "fill_ratio": 0.0, "actuator_balance": 0.0,
            }

        occupied = body != 0
        voxels = int(np.sum(occupied))
        h_actuators = int(np.sum(body == 3))
        v_actuators = int(np.sum(body == 4))
        actuators = h_actuators + v_actuators
        material_types = int(len([m for m in np.unique(body) if m != 0]))
        if voxels > 0:
            rows = np.where(np.any(occupied, axis=1))[0]
            cols = np.where(np.any(occupied, axis=0))[0]
            height = int(rows[-1] - rows[0] + 1)
            width = int(cols[-1] - cols[0] + 1)
            bbox_area = max(1, height * width)
            fill_ratio = float(voxels / bbox_area)
        else:
            height = width = 0
            fill_ratio = 0.0
        actuator_balance = 0.0
        if actuators > 0:
            actuator_balance = 1.0 - abs(h_actuators - v_actuators) / actuators
        return {
            "voxels": voxels,
            "h_actuators": h_actuators,
            "v_actuators": v_actuators,
            "actuators": actuators,
            "material_types": material_types,
            "width": width,
            "height": height,
            "fill_ratio": fill_ratio,
            "actuator_balance": float(actuator_balance),
        }

    def apply_thesis_fitness(self, individuals):
        """
        Shape the existing fitness toward thesis-useful robots.

        This does not replace locomotion. It multiplies the already-computed
        base fitness, so large but immobile bodies are not rescued by size alone.
        Extra attributes are stored for later analysis/export.
        """
        for ind in individuals:
            base = float(getattr(ind, "fitness", getattr(ind, "displacement", 0.0)))
            ind.base_fitness = base

            stats = self._morphology_stats(ind)
            for name, value in stats.items():
                setattr(ind, f"morph_{name}", value)

            if not np.isfinite(base):
                ind.fitness = float("-inf")
                ind.thesis_fitness = ind.fitness
                continue

            displacement = float(getattr(ind, "displacement", 0.0))
            if not np.isfinite(displacement):
                displacement = 0.0

            size_score = min(stats["voxels"] / max(1, self.target_voxels), 1.0)
            actuator_score = min(stats["actuators"] / max(1, self.min_actuators), 1.0)
            material_score = min(stats["material_types"] / max(1, self.min_material_types), 1.0)
            span_score = min(max(stats["width"], stats["height"]) / max(1, int(self.cube_face_size)), 1.0)
            complexity_score = (
                0.35 * material_score
                + 0.35 * stats["actuator_balance"]
                + 0.30 * span_score
            )

            constraint_factor = 1.0
            if stats["voxels"] < self.min_voxels:
                constraint_factor *= max(0.05, stats["voxels"] / max(1, self.min_voxels))
            if stats["actuators"] < self.min_actuators:
                constraint_factor *= max(0.05, stats["actuators"] / max(1, self.min_actuators))
            if stats["material_types"] < 2:
                constraint_factor *= 0.50
            if displacement <= self.move_epsilon:
                constraint_factor *= self.immobile_factor

            morph_multiplier = (
                1.0
                + self.size_weight * size_score
                + self.actuator_weight * actuator_score
                + self.complexity_weight * complexity_score
            )

            ind.size_score = float(size_score)
            ind.actuator_score = float(actuator_score)
            ind.material_score = float(material_score)
            ind.complexity_score = float(complexity_score)
            ind.constraint_factor = float(constraint_factor)
            ind.morph_multiplier = float(morph_multiplier)
            ind.thesis_fitness = float(base * morph_multiplier * constraint_factor)
            ind.fitness = ind.thesis_fitness

    def tournament_selection(self, population, k):
        return max(self.rng.sample(population, k), key=lambda ind: ind.fitness)

    def run(self):
        super().recover_db()
        last_gen, recovered_population = self._recover_state()

        if recovered_population is None:
            generation = 1
            population = self.initialize_population(self.population_size, generation)

            for ind in population:
                ind.phenotype, ind.phase_grid = self.develop_phenotype(ind.genome, self.voxel_types)
                genopheno_abs_metrics(ind, self.args)
                if self.args.run_simulation and _is_simulatable(ind):  
                    prepare_robot_files(ind, self.args)

            if self.args.run_simulation:
                valid_pop = [ind for ind in population if _is_simulatable(ind)]
                invalid_pop = [ind for ind in population if not _is_simulatable(ind)]
                for ind in invalid_pop:
                    ind.displacement = float('-inf')
                ready_pop = [ind for ind in valid_pop if ind.evogym_structure is not None]  
                simulate_evogym_batch(ready_pop, self.args)

            for ind in population:
                behavior_abs_metrics(ind)

            self.update_novelty_archive(population)
            relative_metrics(population, self.args, generation, novelty_archive=self.novelty_archive)
            #self.apply_thesis_fitness(population)
            self._persist_generation_atomic(generation, population, population)
            start_gen = generation + 1
            print(f"Finished generation {generation}.")

        else:
            population = recovered_population
            start_gen = last_gen + 1
            print(
                f"Recovered last completed generation = {last_gen}, "
                f"population size = {len(population)}, next id = {self.id_counter + 1}"
            )

        for generation in range(start_gen, self.num_generations + 1):
            offspring = []
            for _ in range(self.offspring_size):
                parent1 = self.tournament_selection(population, self.tournament_k)
                co_attempts = 0
                while True and co_attempts < 10:
                    parent2 = self.tournament_selection(population, self.tournament_k)
                    if parent2.id != parent1.id:
                        break
                    co_attempts += 1

                child = self.crossover(parent1, parent2)
                child.born_generation = generation
                self.mutate(child)
                child.phenotype, child.phase_grid = self.develop_phenotype(child.genome, self.voxel_types)
                #self._inherit_phase_grid(child, parent1, parent2)  #temporarily off
                genopheno_abs_metrics(child, self.args)
                if self.args.run_simulation and _is_simulatable(child):  
                    prepare_robot_files(child, self.args)

                offspring.append(child)

            if self.args.run_simulation:
                valid_off = [ind for ind in offspring if _is_simulatable(ind)]
                invalid_off = [ind for ind in offspring if not _is_simulatable(ind)]
                for ind in invalid_off:
                    ind.displacement = float('-inf')
                ready_off = [ind for ind in valid_off if ind.evogym_structure is not None]  
                simulate_evogym_batch(ready_off, self.args)

            for ind in offspring:
                behavior_abs_metrics(ind)

            self.update_novelty_archive(offspring)
            pool = population + offspring
            relative_metrics(pool, self.args, generation, novelty_archive=self.novelty_archive)
            #self.apply_thesis_fitness(pool)

            new_population = []
            pool = pool.copy()
            for _ in range(self.population_size):
                k = min(self.tournament_k, len(pool))
                contestants = self.rng.sample(pool, k)
                winner = max(contestants, key=lambda ind: ind.fitness)
                new_population.append(winner)
                pool.remove(winner)

            if self.elitism:
                elite = max(population + offspring, key=lambda ind: ind.fitness)
                if elite not in new_population:
                    idx = self.rng.randrange(len(new_population))
                    new_population.pop(idx)
                    new_population.append(elite)

            population = new_population
            relative_metrics(population, self.args, generation, novelty_archive=self.novelty_archive)
            #self.apply_thesis_fitness(population)
            self._persist_generation_atomic(generation, offspring, population)
            print(f"Finished generation {generation}.")

        try:
            self.session.close()
        except Exception:
            pass

        path_robots = f"{self.args.out_path}/{self.args.study_name}/{self.args.experiment_name}/run_{self.args.run}/robots"
        if os.path.exists(path_robots):
            shutil.rmtree(path_robots)

        print("Finished optimizing.")

    def update_novelty_archive(self, individuals):
        k = max(1, int(round(self.archive_add_frac * len(individuals))))
        chosen = self.rng.sample(individuals, k)
        self.novelty_archive.extend(chosen)

if __name__ == "__main__":
    start = time.time()
    EA().run()
    end = time.time()

    elapsed = end - start
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = elapsed % 60
    print(f"\n[RUN-TIME] {hours}h {minutes}m {seconds:.1f}s")