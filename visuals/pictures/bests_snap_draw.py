import os, sys, json, sqlite3
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT))
from algorithms.GRN_2D import GRN

MAINPATH = "/mnt/c/Users/mo-ou/OneDrive/Documenten/Schoolgerelateerde Documenten/Year 3/Thesis/evogym-GRN/algorithms/tmp_out/defaultstudy"
OUTDIR   = "/mnt/c/Users/mo-ou/OneDrive/Documenten/Schoolgerelateerde Documenten/Year 3/Thesis/evogym-GRN/analysis/plots/robot_visuals"
os.makedirs(OUTDIR, exist_ok=True)

EXPERIMENTS = {
    "Displacement fitness (3×3)":     ("Displacement fitness (3x3)",     3,  9),
    "Reward & penalty fitness (3×3)": ("Reward & penalty fitness (3x3)", 3,  9),
    "Displacement fitness (5×5)":     ("Displacement fitness (5×5)",     5, 25),
    "Reward & penalty fitness (5×5)": ("Reward & penalty fitness (5×5)", 5, 25),
}

# Material ID → color and label
VOXEL_COLORS = {
    0: None,           # empty
    1: ("#6d6d6d", "Bone"),
    2: ("#f5c97a", "Fat"),
    3: ("#e05c5c", "Phase muscle"),
    4: ("#5c8fe0", "Off-phase muscle"),
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


def draw_robot(grid, title, ax):
    rows, cols = grid.shape
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)

    for r in range(rows):
        for c in range(cols):
            vtype = grid[r, c]
            if vtype == 0:
                continue
            color, _ = VOXEL_COLORS[vtype]
            rect = patches.FancyBboxPatch(
                (c + 0.05, rows - r - 1 + 0.05), 0.9, 0.9,
                boxstyle="round,pad=0.05",
                linewidth=0.8,
                edgecolor="#333333",
                facecolor=color,
            )
            ax.add_patch(rect)

    # Grid lines
    for r in range(rows + 1):
        ax.axhline(r, color="#cccccc", linewidth=0.3, zorder=0)
    for c in range(cols + 1):
        ax.axvline(c, color="#cccccc", linewidth=0.3, zorder=0)


def get_best_robot(db_path):
    """Return genome of the robot with highest displacement in the final generation."""
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
    return row  # (genome_json, displacement, robot_id)


# ── Draw a 2×2 panel of best robots ──────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(10, 10))
axes = axes.flatten()

for ax, (label, (folder, cube_face_size, max_voxels)) in zip(axes, EXPERIMENTS.items()):
    db_path = os.path.join(MAINPATH, folder, "run_1", "run_1")
    if not os.path.exists(db_path):
        print(f"Missing: {db_path}")
        ax.axis("off")
        continue

    genome_raw, displacement, robot_id = get_best_robot(db_path)
    genome_list = json.loads(genome_raw)
    grid = develop(genome_list, cube_face_size, max_voxels)

    title = f"{label}\nBest robot — displacement: {displacement:.3f} m"
    draw_robot(grid, title, ax)
    print(f"Drew {label}  (robot_id={robot_id}, disp={displacement:.3f})")

# Shared legend
legend_elements = [
    patches.Patch(facecolor=c, edgecolor="#333", label=l)
    for vt, val in VOXEL_COLORS.items() if val is not None
    for c, l in [val]
]
fig.legend(handles=legend_elements, loc="lower center", ncol=4,
           fontsize=10, frameon=True, bbox_to_anchor=(0.5, 0.01))

plt.suptitle("Best-performing robots per experimental condition\n(final generation, run 1)",
             fontsize=13, fontweight="bold", y=0.98)
plt.tight_layout(rect=[0, 0.06, 1, 0.96])
out = os.path.join(OUTDIR, "best_robots_panel.png")
plt.savefig(out, dpi=200, bbox_inches="tight")
plt.close()
print(f"\nSaved: {out}")

# ── Also save individual robot PNGs ──────────────────────────────────────────
for label, (folder, cube_face_size, max_voxels) in EXPERIMENTS.items():
    db_path = os.path.join(MAINPATH, folder, "run_1", "run_1")
    if not os.path.exists(db_path):
        continue
    genome_raw, displacement, robot_id = get_best_robot(db_path)
    grid = develop(json.loads(genome_raw), cube_face_size, max_voxels)

    fig, ax = plt.subplots(figsize=(4, 4))
    draw_robot(grid, f"{label}\nDisplacement: {displacement:.3f} m", ax)
    legend_elements = [
        patches.Patch(facecolor=c, edgecolor="#333", label=l)
        for vt, (c, l) in VOXEL_COLORS.items() if vt != 0
    ]
    fig.legend(handles=legend_elements, loc="lower center", ncol=2,
               fontsize=8, frameon=True, bbox_to_anchor=(0.5, 0.0))
    plt.tight_layout(rect=[0, 0.12, 1, 1])
    slug = label.replace(" ", "_").replace("×","x").replace("&","and").replace("/","_")
    out = os.path.join(OUTDIR, f"best_{slug}.png")
    plt.savefig(out, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved individual: {out}")