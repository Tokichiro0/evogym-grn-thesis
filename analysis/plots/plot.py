import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

CSV_PATH = "intricacy_per_gen_final.csv"
PLOTDIR  = "plots_5x5"
os.makedirs(PLOTDIR, exist_ok=True)

EXPERIMENTS_5x5 = [
    "Displacement fitness (5×5)",
    "Reward & penalty fitness (5×5)",
]

COLORS = {
    "Displacement fitness (5×5)": "#2e6fa3",
    "Reward & penalty fitness (5×5)": "#b85c1e",
}

LINESTYLES = {
    "Displacement fitness (5×5)": "-",
    "Reward & penalty fitness (5×5)": "-",
}

print("Loading CSV...")
df = pd.read_csv(CSV_PATH, low_memory=False)
df = df.replace([np.inf, -np.inf], np.nan)
df = df[df["experiment"].isin(EXPERIMENTS_5x5)]
print(f"Loaded {len(df)} rows for 5×5 conditions.")

def gen_stats(df, exps, metric):
    sub = df[df["experiment"].isin(exps)].dropna(subset=[metric])
    per_run = sub.groupby(["experiment", "run", "generation"])[metric].median().reset_index()
    return per_run.groupby(["experiment", "generation"])[metric].agg(
        median="median",
        q25=lambda x: x.quantile(0.25),
        q75=lambda x: x.quantile(0.75),
    ).reset_index()

def make_plot(metric, ylabel, title, fname):
    stats = gen_stats(df, EXPERIMENTS_5x5, metric)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for exp in EXPERIMENTS_5x5:
        s = stats[stats["experiment"] == exp].sort_values("generation")
        if s.empty:
            continue
        ax.plot(s["generation"], s["median"],
                color=COLORS[exp], linestyle=LINESTYLES[exp],
                label=exp, linewidth=2)
        ax.fill_between(s["generation"], s["q25"], s["q75"],
                        color=COLORS[exp], alpha=0.15)
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

METRICS = [
    ("fitness", "Fitness", "Fitness over Generations — 5×5 grid", "5x5_fitness.png"),
    ("displacement", "Displacement (m)", "Displacement over Generations — 5×5 grid", "5x5_displacement.png"),
    ("num_voxels", "Number of voxels", "Body Size over Generations — 5×5 grid", "5x5_size.png"),
    ("intricacy", "Intricacy", "Morphological Intricacy over Generations — 5×5 grid", "5x5_intricacy.png"),
    ("intricacy_per_voxel", "Intricacy per voxel", "Intricacy per Voxel over Generations — 5×5 grid", "5x5_intricacy_per_voxel.png"),
]

for metric, ylabel, title, fname in METRICS:
    make_plot(metric, ylabel, title, fname)

last_gen = df["generation"].max()
scatter_df = df[df["generation"] == last_gen].dropna(subset=["intricacy", "displacement"])

fig, ax = plt.subplots(figsize=(8, 6))
for exp in EXPERIMENTS_5x5:
    g = scatter_df[scatter_df["experiment"] == exp]
    ax.scatter(g["intricacy"], g["displacement"],
               color=COLORS[exp], alpha=0.5, s=30,
               label=exp, edgecolors="none")
ax.set_xlabel("Intricacy (boundary right-angle turns)", fontsize=12)
ax.set_ylabel("Displacement (m)", fontsize=12)
ax.set_title("Displacement vs Intricacy — Final Generation (5×5 grid)",
             fontsize=13, fontweight="bold", pad=10)
ax.legend(fontsize=10, title="Experiment", title_fontsize=10, framealpha=0.9)
ax.grid(True, alpha=0.25, linestyle="--")
plt.tight_layout()
path = os.path.join(PLOTDIR, "5x5_scatter_disp_vs_intricacy.png")
plt.savefig(path, dpi=200, bbox_inches="tight")
plt.close()
print("Saved: 5x5_scatter_disp_vs_intricacy.png")
print(f"\nAll plots saved to {PLOTDIR}")