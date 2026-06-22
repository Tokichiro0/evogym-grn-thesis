import numpy as np
import sys
from pathlib import Path
from sklearn.neighbors import KDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from algorithms.voxel_types import VOXEL_TYPES, VOXEL_TYPES_NOBONE

METRICS_ABS = [
    "genome_size",
    "displacement",
    "num_voxels",
    "bone_count",
    "bone_prop",
    "fat_count",
    "fat_prop",
    "fat2_count",
    "fat2_prop",
    "phase_muscle_count",
    "phase_muscle_prop",
    "offphase_muscle_count",
    "offphase_muscle_prop",
]

METRICS_REL = [
    "uniqueness",
    "fitness",
    "age",
    "dominated_disp_nov",
    "novelty",
    "novelty_weighted",
]

def relative_metrics(population, args, generation, novelty_archive=None):
    uniqueness(population)
    novelty(population, novelty_archive)
    novelty_weighted(population)
    age(population, generation)
    pareto_dominance_count(
        population,
        objectives=(("novelty", "max"), ("displacement", "max")),
        out_attr="dominated_disp_nov",
    )
    set_fitness(population, args.fitness_metric)

def genopheno_abs_metrics(individual, args):
    genome_size(individual)
    num_voxels(individual)
    update_material_metrics(individual, args)
    test_validity(individual)

def behavior_abs_metrics(population):
    pass

def update_material_metrics(individual, args):
    if args.voxel_types == "withbone":
        voxel_types = VOXEL_TYPES
    else:
        voxel_types = VOXEL_TYPES_NOBONE

    grid = np.asarray(individual.phenotype, dtype=int)
    filled_total = int((grid != 0).sum())
    individual.filled_total = filled_total

    for name, mid in voxel_types.items():
        count = int((grid == mid).sum())
        prop = (count / filled_total) if filled_total > 0 else 0.0
        setattr(individual, f"{name}_count", count)
        setattr(individual, f"{name}_prop", round(prop, 2))

    for name in ["bone", "fat", "fat2", "phase_muscle", "offphase_muscle"]:
        if not hasattr(individual, f"{name}_count"):
            setattr(individual, f"{name}_count", 0)
        if not hasattr(individual, f"{name}_prop"):
            setattr(individual, f"{name}_prop", 0.0)


def set_fitness(population, fitness_metric):
    for ind in population:
        displacement = float(getattr(ind, "displacement", 0.0) or 0.0)
        num_voxels_val = float(getattr(ind, "num_voxels", 0) or 0)
        bone_count = int(getattr(ind, "bone_count", 0) or 0)
        fat_count = int(getattr(ind, "fat_count", 0) or 0)
        fat2_count = int(getattr(ind, "fat2_count", 0) or 0)
        phase_count = int(getattr(ind, "phase_muscle_count", 0) or 0)
        offphase_count = int(getattr(ind, "offphase_muscle_count", 0) or 0)
        novelty_val = float(getattr(ind, "novelty", 0.0) or 0.0)

        has_rigid = bone_count > 0
        has_soft = (fat_count + fat2_count) > 0
        has_h = phase_count > 0
        has_v = offphase_count > 0

        size_bonus = 0.30 * min(num_voxels_val, 18.0)

        material_bonus = 0.0
        if has_rigid:
            material_bonus += 0.35
        if has_soft:
            material_bonus += 0.35
        if has_h:
            material_bonus += 0.45
        if has_v:
            material_bonus += 0.45
        if has_h and has_v:
            material_bonus += 0.60
        if has_rigid and has_soft and has_h and has_v:
            material_bonus += 0.80

        actuator_balance_bonus = 0.0
        total_act = phase_count + offphase_count
        if total_act > 0:
            balance = 1.0 - abs(phase_count - offphase_count) / total_act
            actuator_balance_bonus = 0.5 * balance

        medium_body_bonus = 1.5 if 10 <= num_voxels_val <= 24 else 0.0
        tiny_body_penalty = -4.0 if num_voxels_val < 8 else 0.0

        no_actuator_penalty = 0.0
        if total_act < 2:
            no_actuator_penalty = -2.5

        invalid_penalty = 0.0
        if not getattr(ind, "valid", False):
            invalid_penalty = -100.0

        if fitness_metric == "baseline":
            ind.fitness = displacement

        elif fitness_metric == "rewards":
            ind.fitness = (
                displacement
                + material_bonus
                + actuator_balance_bonus
                + no_actuator_penalty
                + invalid_penalty
            )

        elif fitness_metric == "novelty":
            ind.fitness = novelty_val

        elif fitness_metric == "novelty_weighted":
            ind.fitness = float(getattr(ind, "novelty_weighted", 0.0) or 0.0)

        elif fitness_metric == "dominated_disp_nov":
            ind.fitness = float(getattr(ind, "dominated_disp_nov", 0.0) or 0.0)

        else:
            ind.fitness = float(getattr(ind, fitness_metric, displacement) or 0.0)


def test_validity(individual):
    total_act = getattr(individual, "phase_muscle_count", 0) + getattr(individual, "offphase_muscle_count", 0)
    individual.valid = total_act >= 1

def age(population, generation):
    for ind in population:
        ind.age = generation - ind.born_generation + 1


def genome_size(individual):
    individual.genome_size = len(individual.genome)

def num_voxels(individual):
    individual.num_voxels = int((individual.phenotype != 0).sum())


def distance(g1, g2):
    a = np.asarray(g1)
    b = np.asarray(g2)

    if a.ndim > 2:
        a = a[-1]
    if b.ndim > 2:
        b = b[-1]

    if a.shape != b.shape:
        raise ValueError(f"Shape mismatch: {a.shape} vs {b.shape}")

    one_zero = (a == 0) ^ (b == 0)
    both_nonzero_diff = (a != 0) & (b != 0) & (a != b)
    return float(one_zero.sum() + 0.5 * both_nonzero_diff.sum())

def uniqueness(population):
    for i, ind in enumerate(population):
        distances = []
        for j, other in enumerate(population):
            if i != j:
                d = distance(ind.phenotype, other.phenotype)
                distances.append(d / max(ind.num_voxels, other.num_voxels))
        ind.uniqueness = np.mean(distances) if distances else 0.0

def novelty_weighted(population):
    beta = 0.05
    for ind in population:
        novelty_weighted = ind.displacement * ind.novelty + beta * ind.displacement
        ind.novelty_weighted = novelty_weighted

def novelty(population, novelty_archive, k=5, M=50, embed_fn=None):
    pool = list(population) + list(novelty_archive or [])

    if embed_fn is None:
        embed_fn = lambda ind: np.array([ind.num_voxels], dtype=np.float32)

    X = np.vstack([embed_fn(ind) for ind in pool]).astype(np.float32)
    tree = KDTree(X)

    for ind in population:
        qi = embed_fn(ind).reshape(1, -1)
        _, idxs = tree.query(qi, k=min(M + 1, len(pool)))
        idxs = idxs[0]

        dists = []
        for j in idxs:
            other = pool[j]
            if other is ind:
                continue
            d = distance(ind.phenotype, other.phenotype)
            dists.append(d / max(ind.num_voxels, other.num_voxels))

        kk = min(k, len(dists))
        ind.novelty = (
            float(np.partition(np.asarray(dists, dtype=np.float32), kk - 1)[:kk].mean())
            if kk
            else 0.0
        )

def pareto_dominance_count(
    population,
    objectives=(("age", "min"), ("displacement", "max")),
    out_attr="dominates_count",
):
    obj_specs = []
    for attr, direction in objectives:
        d = direction.strip().lower()
        obj_specs.append((attr, d))

    def dominates(a, b) -> bool:
        no_worse_all = True
        strictly_better_any = False

        for attr, d in obj_specs:
            av = getattr(a, attr)
            bv = getattr(b, attr)

            if d == "min":
                if av > bv:
                    no_worse_all = False
                    break
                if av < bv:
                    strictly_better_any = True
            else:
                if av < bv:
                    no_worse_all = False
                    break
                if av > bv:
                    strictly_better_any = True

        return no_worse_all and strictly_better_any

    for ind in population:
        setattr(ind, out_attr, 0)

    n = len(population)
    for i in range(n):
        a = population[i]
        cnt = 0
        for j in range(n):
            if i == j:
                continue
            if dominates(a, population[j]):
                cnt += 1
        setattr(a, out_attr, cnt)