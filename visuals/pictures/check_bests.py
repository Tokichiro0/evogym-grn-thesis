import os, sys, json, sqlite3
import numpy as np
from pathlib import Path

sys.path.insert(0, "/mnt/c/Users/mo-ou/OneDrive/Documenten/Schoolgerelateerde Documenten/Year 3/Thesis/evogym-GRN")

from algorithms.GRN_2D import GRN
import evogym.envs
from evogym import get_full_connectivity
import gymnasium as gym
from PIL import Image

MAINPATH = "/mnt/c/Users/mo-ou/OneDrive/Documenten/Schoolgerelateerde Documenten/Year 3/Thesis/evogym-GRN/algorithms/tmp_out/defaultstudy"
OUTDIR   = "/mnt/c/Users/mo-ou/OneDrive/Documenten/Schoolgerelateerde Documenten/Year 3/Thesis/evogym-GRN/analysis/plots/robot_visuals"
os.makedirs(OUTDIR, exist_ok=True)

EXPERIMENTS = {
    "Displacement fitness (5×5)":     ("Displacement fitness (5×5)",     5, 25,  6),
    "Reward & penalty fitness (5×5)": ("Reward & penalty fitness (5×5)", 5, 25, 10),
}

def develop(genome_list, cube_face_size, max_voxels):
    phenotype = GRN(
        promoter_threshold=0.95,
        max_voxels=max_voxels,
        cube_face_size=cube_face_size,
        voxel_types="withbone",
        genotype=genome_list,
        env_conditions=[],
        plastic=False,
    ).develop()
    grid = np.zeros(phenotype.shape, dtype=int)
    for idx, val in np.ndenumerate(phenotype):
        grid[idx] = val.voxel_type if val != 0 else 0
    return grid

def get_best_robot(db_path):
    con = sqlite3.connect(db_path)
    max_gen = con.execute("SELECT MAX(generation) FROM generation_survivors").fetchone()[0]
    row = con.execute("""
        SELECT r.genome, r.displacement, gs.robot_id
        FROM generation_survivors gs
        JOIN all_robots r ON r.robot_id = gs.robot_id
        WHERE gs.generation = ?
        ORDER BY r.displacement DESC
        LIMIT 1
    """, (max_gen,)).fetchone()
    con.close()
    return row

for label, (folder, cube_face_size, max_voxels, best_run) in EXPERIMENTS.items():
    db_path = os.path.join(MAINPATH, folder, f"run_{best_run}", f"run_{best_run}")
    if not os.path.exists(db_path):
        print(f"Missing: {db_path}")
        continue

    print(f"Processing: {label}")
    genome_raw, displacement, robot_id = get_best_robot(db_path)
    grid = develop(json.loads(genome_raw), cube_face_size, max_voxels)
    connections = get_full_connectivity(grid)

    env = gym.make("Walker-v0", body=grid, connections=connections, render_mode="rgb_array")
    obs, _ = env.reset()

    b, A, T = 1.0, 0.4, 20
    for step in range(100):
        action = np.zeros(env.action_space.shape)
        actuator_idx = 0
        for r in range(grid.shape[0]):
            for c in range(grid.shape[1]):
                if grid[r, c] in (3, 4):
                    phase = 0.0 if grid[r, c] == 3 else np.pi
                    val = b + A * np.sin(2 * np.pi * step / T + phase)
                    action[actuator_idx] = np.clip(val, 0.6, 1.6)
                    actuator_idx += 1
        obs, _, terminated, truncated, _ = env.step(action)
        if terminated or truncated:
            break

    img = env.render()
    env.close()

    if img is not None:
        slug = label.replace(" ", "_").replace("(","").replace(")","").replace("&","and")
        out = os.path.join(OUTDIR, f"screenshot_{slug}.png")
        Image.fromarray(img).save(out)
        print(f"  Saved: {out}  (robot_id={robot_id}, disp={displacement:.3f})")
    else:
        print(f"  No render output for {label}")