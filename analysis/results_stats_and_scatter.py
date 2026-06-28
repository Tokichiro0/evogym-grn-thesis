import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu, pearsonr

CSV_PATH = "intricacy_per_gen_final.csv"

df = pd.read_csv(CSV_PATH)

print("Columns in CSV:")
print(df.columns.tolist())

print("\nExperiments:")
print(df["experiment"].unique())

baseline_name = "Displacement fitness (5×5)"
reward_name = "Reward & penalty fitness (5×5)"

df = df[df["experiment"].isin([baseline_name, reward_name])].copy()

for col in ["fitness", "displacement", "num_voxels", "intricacy", "intricacy_per_voxel", "intricacy_per_perimeter"]:
    df = df[np.isfinite(df[col])]

champ_idx = df.groupby(["experiment", "run", "generation"])["fitness"].idxmax()
champions = df.loc[champ_idx].copy()

print("\nChampion rows:")
print(champions.groupby(["experiment", "generation"]).size().tail())


def report_mannwhitney(metric, generation, label):
    sub = champions[champions["generation"] == generation]

    baseline = sub[sub["experiment"] == baseline_name][metric].dropna()
    reward = sub[sub["experiment"] == reward_name][metric].dropna()

    print(f"\n{label}")
    print(f"n displacement-only: {len(baseline)}")
    print(f"n reward & penalty: {len(reward)}")
    print(f"Displacement-only median: {baseline.median():.3f}")
    print(f"Reward & penalty median: {reward.median():.3f}")

    stat, p = mannwhitneyu(baseline, reward, alternative="two-sided")
    print(f"p-value: {p:.3f}")


report_mannwhitney("displacement", 20, "Generation 20 displacement")
report_mannwhitney("displacement", 150, "Generation 150 displacement")
report_mannwhitney("num_voxels", 150, "Generation 150 body size")
report_mannwhitney("intricacy", 150, "Generation 150 raw intricacy")
report_mannwhitney("intricacy_per_voxel", 150, "Generation 150 intricacy per voxel")
report_mannwhitney("intricacy_per_perimeter", 150, "Generation 150 intricacy per perimeter")


final_df = df[df["generation"] == 150].copy()

valid = final_df[["intricacy", "displacement"]].dropna()
valid = valid[np.isfinite(valid["intricacy"]) & np.isfinite(valid["displacement"])]

x = valid["intricacy"]
y = valid["displacement"]

if len(valid) >= 3 and x.nunique() > 1 and y.nunique() > 1:
    r, p = pearsonr(x, y)
    print("\nPearson correlation: final displacement vs raw intricacy")
    print("Using all final-generation individuals")
    print(f"n = {len(valid)}")
    print(f"r = {r:.3f}")
    print(f"p = {p:.3f}")
else:
    r, p = np.nan, np.nan
    print("\nPearson correlation could not be calculated.")


plt.figure(figsize=(7, 5))

for experiment, group in final_df.groupby("experiment"):
    plt.scatter(
        group["intricacy"],
        group["displacement"],
        label=experiment,
        alpha=0.35,
        s=25
    )

if len(valid) >= 3 and x.nunique() > 1:
    coeffs = np.polyfit(x, y, 1)
    trend = np.poly1d(coeffs)

    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = trend(x_line)

    plt.plot(
        x_line,
        y_line,
        linestyle="--",
        linewidth=2,
        label="Linear trend"
    )

plt.xlabel("Raw morphological intricacy")
plt.ylabel("Displacement")
plt.title("Displacement vs raw intricacy, final generation")
plt.legend(fontsize=8, loc="best")
plt.tight_layout()

OUT_PATH = "5x5_scatter_disp_vs_intricacy_trend.png"
plt.savefig(OUT_PATH, dpi=300)

print(f"\nSaved updated figure to: {os.path.abspath(OUT_PATH)}")