# GRN-Developed Soft Robots in EvoGym

This repository contains the code, final experiment outputs, plots, statistics, and videos used for my bachelor thesis on evolving 2D soft robots with a Gene Regulatory Network (GRN) developmental encoding in EvoGym.

Repository: https://github.com/Tokichiro0/evogym-grn-thesis

## Research Questions

**RQ1:** Does displacement-based selection in GRN-developed soft robots create pressure toward smaller and simpler morphologies?

**RQ2:** If so, can reward shaping produce larger and more intricate bodies without reducing locomotion performance?

## Project Overview

The thesis compares two fitness functions in a `5x5` EvoGym voxel design space:

- **Displacement fitness:** selection is based only on forward displacement.
- **Reward & penalty fitness:** displacement is combined with rewards for material diversity, sufficient actuation, actuator balance, and valid morphology.

The goal is to test whether displacement-only selection favors compact robots, and whether reward shaping can produce larger robots without significantly reducing final locomotion performance.

## Repository Structure

```text
evogym-grn-thesis/
├── algorithms/
│   ├── basic_EA_thesis.py
│   ├── GRN_2D.py
│   └── tmp_out/defaultstudy/
│       ├── Displacement fitness (5×5)/
│       └── Reward & penalty fitness (5×5)/
│
├── simulation/
│   ├── prepare_robot_files.py
│   └── simulation_resources.py
│
├── utils/
│   ├── config.py
│   ├── metrics.py
│   └── draw.py
│
├── analysis/
│   ├── intricacy.py
│   ├── phase_grids.py
│   ├── results_stats_and_scatter.py
│   ├── intricacy_per_gen_final.csv
│   └── plots/
│
├── visuals/
│   ├── pictures/
│   └── videos/
│
├── requirements.txt
└── README.md
```

## Main Files

| File | Purpose |
|---|---|
| `algorithms/basic_EA_thesis.py` | Main evolutionary algorithm |
| `algorithms/GRN_2D.py` | GRN development from genome to voxel body and phase grid |
| `simulation/prepare_robot_files.py` | Converts GRN phenotypes to EvoGym robots |
| `simulation/simulation_resources.py` | Runs EvoGym simulations with a fixed oscillator controller |
| `utils/metrics.py` | Defines displacement and reward & penalty fitness |
| `analysis/intricacy.py` | Calculates boundary intricacy metrics |
| `analysis/phase_grids.py` | Calculates phase/off-phase actuator balance |
| `analysis/results_stats_and_scatter.py` | Runs statistical tests and creates the trend-line scatter plot |
| `analysis/plots/plot.py` | Generates final thesis plots |

## Experiment Setup

| Parameter | Value |
|---|---|
| Environment | `Walker-v0` |
| Grid size | `5x5` |
| Maximum voxels | `25` |
| Population size | `50` |
| Offspring size | `50` |
| Generations | `150` |
| Runs | `10` per condition |
| Simulation steps | `500` |
| Controller | Fixed sine-wave oscillator |

The fixed oscillator controller uses:

```text
action = bias + amplitude * sin(angle + phase)
```

with:

| Parameter | Value |
|---|---|
| Bias | `1.0` |
| Amplitude | `0.4` |
| Period | `20` steps |
| Action range | `[0.6, 1.6]` |

## Material Types

| Value | Material |
|---|---|
| `0` | Empty |
| `1` | Bone / rigid material |
| `2` | Fat / passive soft material |
| `3` | Phase muscle |
| `4` | Off-phase muscle |

## Main Findings

- Displacement-only selection produced smaller final robots.
- Reward & penalty fitness produced significantly larger final robots.
- Final displacement was slightly lower under reward & penalty fitness, but not significantly different.
- Reward & penalty fitness appeared less efficient early in evolution, but final locomotion performance remained comparable.
- Reward & penalty fitness did not significantly increase raw intricacy, normalized intricacy, or actuator balance.
- The reward function mainly increased body size and material variation, not boundary intricacy.


## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

Install EvoGym separately, for example:

```bash
pip install -e ../evogym --no-deps --no-build-isolation
```

## Running Experiments

Run commands from the repository root.

### Displacement Fitness

```bash
python algorithms/basic_EA_thesis.py \
  --experiment_name "Displacement fitness (5×5)" \
  --fitness_metric baseline \
  --population_size 50 \
  --offspring_size 50 \
  --num_generations 150 \
  --cube_face_size 5 \
  --max_voxels 25 \
  --run 1
```

### Reward & Penalty Fitness

```bash
python algorithms/basic_EA_thesis.py \
  --experiment_name "Reward & penalty fitness (5×5)" \
  --fitness_metric rewards \
  --population_size 50 \
  --offspring_size 50 \
  --num_generations 150 \
  --cube_face_size 5 \
  --max_voxels 25 \
  --run 1
```

Repeat both conditions for runs `1` to `10`.

## Analysis Workflow

Run the analysis scripts after the experiments finish:

```bash
python analysis/intricacy.py
python analysis/phase_grids.py
python analysis/results_stats_and_scatter.py
python analysis/plots/plot.py
python analysis/plots/5x5_balance/balance.py
```

Final plots are saved in:

```text
analysis/plots/plots_5x5/
```

Important plots:

```text
5x5_fitness.png
5x5_displacement.png
5x5_size.png
5x5_intricacy.png
5x5_intricacy_per_voxel.png
5x5_scatter_disp_vs_intricacy_trend.png
```

## Included Outputs

The repository includes the final `5x5` outputs used in the thesis:

```text
algorithms/tmp_out/defaultstudy/Displacement fitness (5×5)/
algorithms/tmp_out/defaultstudy/Reward & penalty fitness (5×5)/
analysis/intricacy_per_gen_final.csv
analysis/balance_5x5.csv
analysis/plots/
visuals/pictures/
visuals/videos/
```

Videos and large output files are tracked with Git LFS.

```bash
git lfs install
git lfs pull
```

## Notes

The final thesis analysis focuses only on the `5x5` experiments.

Older `2x2`, `3x3`, and `4x4` outputs were used during development but are not part of the final thesis results.

Some scripts may contain local path variables that need to be updated before running on another machine.

Boundary intricacy measures only the external body outline.

Actuator balance measures only the number of phase and off-phase actuators, not their spatial placement or coordination quality.
