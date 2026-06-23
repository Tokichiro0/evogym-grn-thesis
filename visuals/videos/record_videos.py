import sys, os, math, sqlite3, json, ast
import numpy as np
import gymnasium as gym
import evogym.envs
import imageio

sys.path.insert(0, ".")
from algorithms.GRN_2D import GRN
from simulation.prepare_robot_files import get_full_connectivity

def load_best_robot(db_path):
    conn = sqlite3.connect(db_path)
    row = conn.execute("""
        SELECT ar.genome
        FROM generation_survivors gs
        JOIN all_robots ar ON gs.robot_id = ar.robot_id
        WHERE gs.generation = (SELECT MAX(generation) FROM generation_survivors)
          AND gs.fitness > -1e9
        ORDER BY gs.fitness DESC LIMIT 1
    """).fetchone()
    conn.close()
    genome_raw = row[0]
    genome = ast.literal_eval(genome_raw) if isinstance(genome_raw, str) else genome_raw
    return [float(x) for x in genome]

def develop_robot(genome):
    grn = GRN(
        promoter_threshold=0.95,
        max_voxels=9,
        cube_face_size=3,
        genotype=genome,
        voxel_types="withbone",
        env_conditions=None,
        plastic=0,
    )
    phenotype = grn.develop()
    phenotype_materials = np.zeros(phenotype.shape, dtype=int)
    phase_grid = np.zeros(phenotype.shape, dtype=float)
    for index, value in np.ndenumerate(phenotype):
        if value != 0:
            phenotype_materials[index] = value.voxel_type
            phase_grid[index] = value.phase
    return phenotype_materials, phase_grid

def record_video(structure, phase_offsets, out_path, steps=500):
    from evogym import get_full_connectivity
    connections = get_full_connectivity(structure)

    env = gym.make("Walker-v0", body=structure, connections=connections,
                   render_mode="rgb_array")
    env.reset()
    sim = env.unwrapped.sim

    actuator_indices = sim.get_actuator_indices("robot").astype(int).flatten()
    phase_flat = phase_offsets.reshape(-1)
    actuator_phases = phase_flat[actuator_indices] if actuator_indices.size else np.array([])

    bias, amplitude, period_steps = 1.0, 0.4, 20
    frames = []

    for t in range(steps):
        if actuator_indices.size:
            angle = 2.0 * math.pi * (t / period_steps)
            action = np.clip(bias + amplitude * np.sin(angle + actuator_phases), 0.6, 1.6).astype(np.float64)
        else:
            action = np.array([])
        env.step(action)
        frames.append(env.render())

    env.close()
    imageio.mimwrite(out_path, frames, fps=30)
    print(f"Saved: {out_path}")

base = "algorithms/tmp_out/defaultstudy/Reward & penalty fitness (3x3)"
os.makedirs("videos", exist_ok=True)

for run_num in range(1, 11):
    db_path = os.path.join(base, f"run_{run_num}", f"run_{run_num}")
    print(f"\n=== Run {run_num} ===")
    try:
        genome = load_best_robot(db_path)
        structure, phase_offsets = develop_robot(genome)
        record_video(structure, phase_offsets, f"videos/run_{run_num}_best.mp4")
    except Exception as e:
        print(f"Error: {e}")