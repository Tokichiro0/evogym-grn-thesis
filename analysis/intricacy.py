import os, sys, csv, json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from algorithms.GRN_2D import GRN

MAINPATH = "/mnt/c/Users/mo-ou/OneDrive/Documenten/Schoolgerelateerde Documenten/Year 3/Thesis/evogym-GRN/algorithms/tmp_out/defaultstudy"
PLOTDIR  = "/mnt/c/Users/mo-ou/OneDrive/Documenten/Schoolgerelateerde Documenten/Year 3/Thesis/evogym-GRN/analysis/plots"
os.makedirs(PLOTDIR, exist_ok=True)

#Experiments: display label → (folder name, grid size, max_voxels)
EXPERIMENTS = {
    "Displacement fitness (3×3)":     ("Displacement fitness (3x3)",     3,  9),
    "Reward & penalty fitness (3×3)": ("Reward & penalty fitness (3x3)", 3,  9),
    "Displacement fitness (5×5)":     ("Displacement fitness (5×5)",     5, 25),
    "Reward & penalty fitness (5×5)": ("Reward & penalty fitness (5×5)", 5, 25),
}
COLORS = {
    "Displacement fitness (3×3)":     "#4a90d9",
    "Reward & penalty fitness (3×3)": "#e07b39",
    "Displacement fitness (5×5)":     "#2e6fa3",
    "Reward & penalty fitness (5×5)": "#b85c1e",
}
LINESTYLES = {
    "Displacement fitness (3×3)":     "--",
    "Reward & penalty fitness (3×3)": "--",
    "Displacement fitness (5×5)":     "-",
    "Reward & penalty fitness (5×5)": "-",
}
PROMOTOR_THRESHOLD = 0.95

def develop_phenotype(genome_list, cube_face_size, max_voxels):
    phenotype = GRN(
        promoter_threshold=PROMOTOR_THRESHOLD,
        max_voxels=max_voxels,
        cube_face_size=cube_face_size,
        voxel_types="withbone",
        genotype=genome_list,
        env_conditions=[],
        plastic=False,
    ).develop()
    grid = np.zeros(phenotype.shape, dtype=int)
    for index, value in np.ndenumerate(phenotype):
        grid[index] = value.voxel_type if value != 0 else 0
    return grid

def calc_intricacy_metrics(grid):
    coordinates = list(zip(*np.where(grid != 0)))
    num_voxels = len(coordinates)
    if num_voxels == 0:
        return 0, 0.0, 0.0, 0.0, 0.0
    squares = [
        Polygon([(c-.5,r-.5),(c+.5,r-.5),(c+.5,r+.5),(c-.5,r+.5)])
        for r, c in coordinates
    ]
    union = unary_union(squares)
    if isinstance(union, Polygon):
        boundary_coords = np.array(union.exterior.coords)
        perimeter = float(union.length)
    elif isinstance(union, MultiPolygon):
        boundary_coords = np.vstack([np.array(p.exterior.coords) for p in union.geoms])
        perimeter = float(union.length)
    else:
        return 0, float(num_voxels), 0.0, 0.0, 0.0
    directions = np.diff(boundary_coords, axis=0)
    angles = np.arctan2(directions[:,1], directions[:,0])
    angle_diffs = np.abs((np.diff(np.concatenate((angles,[angles[0]]))) + np.pi) % (2*np.pi) - np.pi)
    intricacy = int(np.sum(np.isclose(angle_diffs, np.pi/2)))
    intricacy_per_voxel    = intricacy / num_voxels if num_voxels > 0 else 0.0
    intricacy_per_perimeter = intricacy / perimeter if perimeter > 0 else 0.0
    return intricacy, float(num_voxels), perimeter, intricacy_per_voxel, intricacy_per_perimeter


#Load all data from DBs 
FIELDNAMES = [
    "experiment", "run", "generation", "robot_id", "fitness", "displacement",
    "num_voxels", "intricacy", "perimeter", "intricacy_per_voxel", "intricacy_per_perimeter"
]

all_rows = []

for label, (folder, cube_face_size, max_voxels) in EXPERIMENTS.items():
    exp_path = os.path.join(MAINPATH, folder)
    if not os.path.exists(exp_path):
        print(f"MISSING: {exp_path}")
        continue

    for run_num in range(1, 11):
        db_path = os.path.join(exp_path, f"run_{run_num}", f"run_{run_num}")
        if not os.path.exists(db_path):
            print(f"  Missing run {run_num} for {label}")
            continue

        print(f"{label}  run {run_num}")
        engine = create_engine(f"sqlite:///{db_path}", future=True)
        with engine.connect() as conn:
            results = conn.execute(text("""
                SELECT gs.generation, gs.robot_id, gs.fitness,
                       r.displacement, r.num_voxels, r.genome
                FROM generation_survivors gs
                JOIN all_robots r ON r.robot_id = gs.robot_id
                ORDER BY gs.generation ASC
            """)).fetchall()
        engine.dispose()

        for row in results:
            gen, robot_id, fitness, displacement, num_voxels, genome_raw = row
            try:
                genome_list = json.loads(genome_raw)
                phenotype   = develop_phenotype(genome_list, cube_face_size, max_voxels)
                intr, _, perimeter, intr_per_voxel, intr_per_peri = calc_intricacy_metrics(phenotype)
            except Exception as e:
                print(f"  ERROR robot {robot_id} gen {gen}: {e}")
                intr = perimeter = intr_per_voxel = intr_per_peri = None

            all_rows.append({
                "experiment":           label,
                "run":                  run_num,
                "generation":           gen,
                "robot_id":             robot_id,
                "fitness":              fitness,
                "displacement":         displacement,
                "num_voxels":           num_voxels,
                "intricacy":            intr,
                "perimeter":            perimeter,
                "intricacy_per_voxel":  intr_per_voxel,
                "intricacy_per_perimeter": intr_per_peri,
            })

#Save CSV file with al metrics
out_csv = os.path.join(MAINPATH, "intricacy_per_gen_final.csv")
with open(out_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(all_rows)
print(f"\nCSV saved -> {out_csv}  ({len(all_rows)} rows)")

#Plotting 
df = pd.DataFrame(all_rows)
df = df.replace([np.inf, -np.inf], np.nan)

PLOT_GROUPS = [
    ("3×3", ["Displacement fitness (3×3)", "Reward & penalty fitness (3×3)"]),
    ("5×5", ["Displacement fitness (5×5)", "Reward & penalty fitness (5×5)"]),
    ("All", list(EXPERIMENTS.keys())),
]

METRICS = [
    ("fitness",              "Fitness",               "Fitness over Generations"),
    ("displacement",         "Displacement (m)",      "Displacement over Generations"),
    ("num_voxels",           "Number of voxels",      "Body Size over Generations"),
    ("intricacy",            "Intricacy",             "Morphological Intricacy over Generations"),
    ("intricacy_per_voxel",  "Intricacy per voxel",  "Intricacy per Voxel over Generations"),
]

def gen_stats(df, exps, metric):
    sub = df[df["experiment"].isin(exps)].dropna(subset=[metric])
    per_run = sub.groupby(["experiment","run","generation"])[metric].median().reset_index()
    return per_run.groupby(["experiment","generation"])[metric].agg(
        median="median",
        q25=lambda x: x.quantile(0.25),
        q75=lambda x: x.quantile(0.75),
    ).reset_index()

def make_plot(metric, ylabel, title, exps, fname):
    stats = gen_stats(df, exps, metric)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for exp in exps:
        s = stats[stats["experiment"] == exp].sort_values("generation")
        if s.empty:
            continue
        ax.plot(s["generation"], s["median"],
                color=COLORS[exp], linestyle=LINESTYLES[exp],
                label=exp, linewidth=2)
        ax.fill_between(s["generation"], s["q25"], s["q75"],
                        color=COLORS[exp], alpha=0.12)
    ax.set_xlabel("Generation", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.legend(fontsize=9, title="Experiment", title_fontsize=9,
              framealpha=0.9, loc="best")
    ax.grid(True, alpha=0.25, linestyle="--")
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    plt.tight_layout()
    path = os.path.join(PLOTDIR, fname)
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved {fname}")

#Per grid-size group + combined
for group_label, exps in PLOT_GROUPS:
    slug = group_label.replace("×","x").replace(" ","_").lower()
    for metric, ylabel, title in METRICS:
        fname = f"{slug}_{metric}.png"
        full_title = f"{title} — {group_label} grid"
        make_plot(metric, ylabel, full_title, exps, fname)

#Scatter: displacement vs intricacy (final generation, per group)
for group_label, exps in PLOT_GROUPS:
    slug = group_label.replace("×","x").replace(" ","_").lower()
    last_gen_df = df[df["experiment"].isin(exps)].dropna(subset=["intricacy","displacement"])
    last_gen_df = last_gen_df[last_gen_df["generation"] == last_gen_df["generation"].max()]
    fig, ax = plt.subplots(figsize=(8, 6))
    for exp in exps:
        g = last_gen_df[last_gen_df["experiment"] == exp]
        ax.scatter(g["intricacy"], g["displacement"],
                   color=COLORS[exp], alpha=0.45, s=25, label=exp,
                   edgecolors="none")
    ax.set_xlabel("Intricacy (boundary right-angle turns)", fontsize=12)
    ax.set_ylabel("Displacement (m)", fontsize=12)
    ax.set_title(f"Displacement vs Intricacy — Final Generation ({group_label} grid)",
                 fontsize=13, fontweight="bold", pad=10)
    ax.legend(fontsize=9, title="Experiment", title_fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.25, linestyle="--")
    plt.tight_layout()
    path = os.path.join(PLOTDIR, f"{slug}_scatter_disp_vs_intricacy.png")
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved {slug}_scatter_disp_vs_intricacy.png")
print(f"\nAll plots saved to {PLOTDIR}")