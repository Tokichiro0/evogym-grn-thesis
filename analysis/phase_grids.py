import os, sys, json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from algorithms.GRN_2D import GRN

MAINPATH = "/mnt/c/Users/mo-ou/OneDrive/Documenten/Schoolgerelateerde Documenten/Year 3/Thesis/evogym-GRN/algorithms/tmp_out/defaultstudy"
PLOTDIR  = "/mnt/c/Users/mo-ou/OneDrive/Documenten/Schoolgerelateerde Documenten/Year 3/Thesis/evogym-GRN/analysis/plots/5x5_balance"
os.makedirs(PLOTDIR, exist_ok=True)

EXPERIMENTS = {
    "Displacement fitness (5×5)":     ("Displacement fitness (5×5)", 5, 25),
    "Reward & penalty fitness (5×5)": ("Reward & penalty fitness (5×5)", 5, 25),
}

COLORS = {
    "Displacement fitness (5×5)":     "#2e6fa3",
    "Reward & penalty fitness (5×5)": "#b85c1e",
}

LINESTYLES = {
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

def actuator_counts_and_balance(grid):
    n_phase = int(np.sum(grid == 3))
    n_offphase = int(np.sum(grid == 4))
    total = n_phase + n_offphase
    if total == 0:
        balance = 0.0
    else:
        balance = 1 - abs(n_phase - n_offphase) / total
    return n_phase, n_offphase, balance

rows = []

for label, (folder, cube_face_size, max_voxels) in EXPERIMENTS.items():
    exp_path = os.path.join(MAINPATH, folder)
    if not os.path.exists(exp_path):
        print(f"MISSING: {exp_path}")
        continue

    for run_num in range(1, 11):
        db_path = os.path.join(exp_path, f"run_{run_num}", f"run_{run_num}")
        if not os.path.exists(db_path):
            print(f"Missing run {run_num} for {label}")
            continue

        print(f"{label} | run {run_num}")
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
                phenotype = develop_phenotype(genome_list, cube_face_size, max_voxels)
                n_phase, n_offphase, balance = actuator_counts_and_balance(phenotype)
            except Exception as e:
                print(f"ERROR robot {robot_id} gen {gen}: {e}")
                n_phase, n_offphase, balance = None, None, None

            rows.append({
                "experiment": label,
                "run": run_num,
                "generation": gen,
                "robot_id": robot_id,
                "fitness": fitness,
                "displacement": displacement,
                "num_voxels": num_voxels,
                "n_phase": n_phase,
                "n_offphase": n_offphase,
                "actuator_balance": balance,
            })

df = pd.DataFrame(rows)
df = df.replace([np.inf, -np.inf], np.nan)

out_csv = os.path.join(PLOTDIR, "balance_5x5.csv")
df.to_csv(out_csv, index=False)
print(f"Saved CSV: {out_csv}")

def gen_stats(df, exps, metric):
    sub = df[df["experiment"].isin(exps)].dropna(subset=[metric])
    per_run = sub.groupby(["experiment", "run", "generation"])[metric].median().reset_index()
    return per_run.groupby(["experiment", "generation"])[metric].agg(
        median="median",
        q25=lambda x: x.quantile(0.25),
        q75=lambda x: x.quantile(0.75),
    ).reset_index()

def make_line_plot(metric, ylabel, title, fname):
    exps = list(EXPERIMENTS.keys())
    stats = gen_stats(df, exps, metric)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for exp in exps:
        s = stats[stats["experiment"] == exp].sort_values("generation")
        if s.empty:
            continue
        ax.plot(
            s["generation"], s["median"],
            color=COLORS[exp], linestyle=LINESTYLES[exp],
            linewidth=2, label=exp
        )
        ax.fill_between(
            s["generation"], s["q25"], s["q75"],
            color=COLORS[exp], alpha=0.15
        )

    ax.set_xlabel("Generation", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.legend(fontsize=10, title="Experiment", title_fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.25, linestyle="--")
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    plt.tight_layout()
    path = os.path.join(PLOTDIR, fname)
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: {fname}")

make_line_plot(
    "actuator_balance",
    "Actuator balance",
    "Phase vs Off-phase Actuator Balance over Generations — 5×5 grid",
    "5x5_actuator_balance.png"
)

last_gen = df["generation"].max()
scatter_df = df[df["generation"] == last_gen].dropna(subset=["actuator_balance", "displacement"])

fig, ax = plt.subplots(figsize=(8, 6))
for exp in EXPERIMENTS.keys():
    g = scatter_df[scatter_df["experiment"] == exp]
    ax.scatter(
        g["actuator_balance"], g["displacement"],
        color=COLORS[exp], alpha=0.5, s=30,
        label=exp, edgecolors="none"
    )

ax.set_xlabel("Actuator balance", fontsize=12)
ax.set_ylabel("Displacement (m)", fontsize=12)
ax.set_title("Displacement vs Actuator Balance — Final Generation (5×5 grid)",
             fontsize=13, fontweight="bold", pad=10)
ax.legend(fontsize=10, title="Experiment", title_fontsize=10, framealpha=0.9)
ax.grid(True, alpha=0.25, linestyle="--")
plt.tight_layout()
path = os.path.join(PLOTDIR, "5x5_scatter_disp_vs_balance.png")
plt.savefig(path, dpi=200, bbox_inches="tight")
plt.close()
print("Saved: 5x5_scatter_disp_vs_balance.png")
print(f"\nAll balance plots saved to {PLOTDIR}")