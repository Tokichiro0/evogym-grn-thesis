import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu
import os

CSV_PATH = "balance_5x5.csv"
OUTDIR = "balance_plots"
os.makedirs(OUTDIR, exist_ok=True)

df = pd.read_csv(CSV_PATH)
df = df.replace([np.inf, -np.inf], np.nan)

experiments = [
    "Displacement fitness (5×5)",
    "Reward & penalty fitness (5×5)"
]

colors = {
    "Displacement fitness (5×5)": "#2e6fa3",
    "Reward & penalty fitness (5×5)": "#b85c1e"
}

def gen_stats(metric):
    sub = df[df["experiment"].isin(experiments)].dropna(subset=[metric])

    # First summarize each run per generation
    per_run = (
        sub.groupby(["experiment", "run", "generation"])[metric]
        .median()
        .reset_index()
    )

    # Then summarize across runs
    stats = (
        per_run.groupby(["experiment", "generation"])[metric]
        .agg(
            median="median",
            q25=lambda x: x.quantile(0.25),
            q75=lambda x: x.quantile(0.75),
        )
        .reset_index()
    )
    return stats

def line_plot(metric, ylabel, title, filename):
    stats = gen_stats(metric)

    plt.figure(figsize=(9, 5))

    for exp in experiments:
        s = stats[stats["experiment"] == exp].sort_values("generation")

        plt.plot(
            s["generation"],
            s["median"],
            label=exp,
            color=colors[exp],
            linewidth=2
        )

        plt.fill_between(
            s["generation"],
            s["q25"],
            s["q75"],
            color=colors[exp],
            alpha=0.15
        )

    plt.xlabel("Generation")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, filename), dpi=200)
    plt.close()

line_plot(
    "actuator_balance",
    "Actuator balance",
    "Phase vs Off-phase Actuator Balance over Generations",
    "5x5_actuator_balance.png"
)

line_plot(
    "n_phase",
    "Number of phase actuators",
    "Phase Actuators over Generations",
    "5x5_n_phase.png"
)

line_plot(
    "n_offphase",
    "Number of off-phase actuators",
    "Off-phase Actuators over Generations",
    "5x5_n_offphase.png"
)