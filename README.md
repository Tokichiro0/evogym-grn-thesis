# GRN-Developed Soft Robots in EvoGym

This repository contains the code, final experiment outputs, analysis scripts, plots, and videos used for my bachelor thesis on evolving 2D soft robots with a Gene Regulatory Network (GRN) developmental encoding in EvoGym.

Code repository: https://github.com/Tokichiro0/evogym-grn-thesis

The project builds on pre-existing EvoGym-GRN source code. My thesis adapts this code to compare two fitness functions in a `5x5` voxel design space:

- displacement-only fitness
- reward & penalty fitness

The goal of the thesis is to investigate whether displacement-based selection creates pressure toward smaller morphologies, and whether reward shaping can produce larger or more structured robots without strongly reducing locomotion performance.

## Research Question

> Does displacement-based selection in GRN-developed soft robots create pressure toward smaller morphologies, and can reward shaping produce more complex bodies without reducing locomotion performance?

## Repository Contents

```text
evogym-grn-thesis/
├── algorithms/
│   ├── basic_EA_thesis.py
│   ├── GRN_2D.py
│   ├── voxel_types.py
│   ├── EA_classes.py
│   ├── experiment.py
│   └── tmp_out/
│       └── defaultstudy/
│           ├── Displacement fitness (5×5)/
│           └── Reward & penalty fitness (5×5)/
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
│   ├── intricacy_per_gen_final.csv
│   ├── results_stats_and_scatter.py  
│   └── plots/
│       ├── plot.py
│       ├── plots_5x5/
│       └── 5x5_balance/
│
├── visuals/
│   ├── pictures/
│   └── videos/
│       ├── 5x5/
│       ├── 5x5_baseline/
│       └── record_videos.py
│
├── experiments/
├── requirements.txt
├── .gitattributes
├── .gitignore
└── README.md
```

The main thesis code is in `algorithms/`, `simulation/`, `utils/`, and `analysis/`.

The `experiments/` folder contains older or supporting scripts from the broader original project. The `visuals/pictures/` folder contains example robot screenshots used for inspection and thesis figures. The `visuals/videos/` folder contains final videos for the thesis-relevant `5x5` runs.

The final raw experiment outputs for the two main `5x5` conditions are included in:

```text
algorithms/tmp_out/defaultstudy/Displacement fitness (5×5)/
algorithms/tmp_out/defaultstudy/Reward & penalty fitness (5×5)/
```

Non-final outputs, such as old `2x2`, `3x3`, and `4x4` runs, are not part of the final thesis analysis and are ignored by Git.

## Main Adaptations

Compared with the original EvoGym-GRN codebase, this thesis version adds or modifies:

- `algorithms/basic_EA_thesis.py` as the main evolutionary algorithm
- GRN development with actuator phase values
- phase and off-phase actuator material types
- conversion from GRN phenotypes to EvoGym robot structures
- EvoGym simulation using a fixed sine-wave controller
- displacement-only fitness
- reward & penalty fitness
- morphology metrics such as body size, material composition, actuator balance, and boundary intricacy
- analysis scripts for final plots, actuator balance, and boundary intricacy
- final videos and raw `5x5` thesis experiment outputs

## Final Experiment Setup

| Parameter | Value |
|---|---|
| Environment | `Walker-v0` |
| Grid size | `5x5` |
| Maximum voxels | `25` |
| Population size | `50` |
| Offspring size | `50` |
| Generations | `150` |
| Runs | `10` per condition |
| Selection | Tournament selection |
| Tournament size | `4` |
| Crossover probability | `1.0` |
| Mutation probability | `0.9` |
| Simulation steps | `500` |
| Controller | Fixed sine-wave controller |

The two final conditions are:

| Condition | Fitness metric |
|---|---|
| Displacement fitness | `baseline` |
| Reward & penalty fitness | `rewards` |

## Main Files

### `algorithms/basic_EA_thesis.py`

The primary evolutionary algorithm used for the thesis experiments. It handles population initialization, parent selection, crossover, mutation, GRN development, EvoGym simulation, fitness calculation, survivor selection, elitism, and result saving.

Mutation is applied before GRN development, so the evaluated phenotype corresponds to the final mutated genome.

### `algorithms/GRN_2D.py`

Contains the GRN developmental encoding. A real-valued genome is decoded into a 2D voxel robot body and a phase grid.

Material values:

| Value | Material |
|---|---|
| `0` | Empty |
| `1` | Bone / rigid material |
| `2` | Fat / passive soft material |
| `3` | Phase muscle |
| `4` | Off-phase muscle |

Important settings:

| Parameter | Value |
|---|---|
| Promoter threshold | `0.95` |
| Development steps | `200` |
| Concentration decay | `0.005` |
| Diffusion sites per cell | `4` |
| Initial genome size | `300` |

### `simulation/prepare_robot_files.py`

Converts the developed GRN phenotype into EvoGym-compatible robot data. It trims empty borders, maps GRN material IDs to EvoGym voxel IDs, creates connectivity, and aligns actuator phase offsets with the final robot body.

### `simulation/simulation_resources.py`

Runs robots in EvoGym `Walker-v0`.

The controller uses:

```text
action = bias + amplitude * sin(angle + phase)
```

Default controller values:

| Parameter | Value |
|---|---|
| Bias | `1.0` |
| Amplitude | `0.4` |
| Period | `20` steps |
| Action range | `[0.6, 1.6]` |

Displacement is measured as forward movement in the x-direction.

### `utils/metrics.py`

Calculates morphology and fitness metrics.

The baseline fitness is:

```text
fitness = displacement
```

The reward & penalty fitness includes:

- displacement
- material diversity bonus
- actuator balance bonus
- penalty for too few actuators
- penalty for invalid morphologies

The reward fitness does not directly reward body size.

### `utils/config.py`

Defines command-line arguments such as population size, number of generations, grid size, maximum voxels, fitness metric, run number, and EvoGym controller settings.

## Analysis Scripts

### `analysis/intricacy.py`

Redevelops saved genomes from experiment databases and calculates boundary-based morphology metrics:

- raw intricacy
- intricacy per voxel
- intricacy per perimeter

### `analysis/phase_grids.py`

Calculates balance between phase and off-phase actuators.

The actuator-balance metric is:

```text
1 - abs(n_phase - n_offphase) / (n_phase + n_offphase)
```

A value of `1.0` means equal numbers of phase and off-phase actuators.  
A value of `0.0` means only one actuator type is present.

### `analysis/plots/plot.py`

Generates the final `5x5` plots, including:

- fitness over generations
- displacement over generations
- body size over generations
- raw intricacy over generations
- intricacy per voxel over generations
- displacement versus intricacy scatter plot

Final plots are saved in:

```text
analysis/plots/plots_5x5/
```

### `analysis/plots/5x5_balance/balance.py`

Generates actuator-balance plots for the final `5x5` experiments.

### `visuals/videos/record_videos.py`

Records videos of selected evolved robots from saved experiment outputs.

## Included Outputs

The repository includes the final files needed for thesis inspection and reproducibility:

```text
analysis/intricacy_per_gen_final.csv
analysis/plots/plots_5x5/
analysis/plots/5x5_balance/
algorithms/tmp_out/defaultstudy/Displacement fitness (5×5)/
algorithms/tmp_out/defaultstudy/Reward & penalty fitness (5×5)/
visuals/pictures/
visuals/videos/5x5/
visuals/videos/5x5_baseline/
visuals/videos/record_videos.py
```

The videos and other large output files are tracked using Git LFS.

## Not Included Outputs

The following non-final outputs are ignored by Git:

```text
algorithms/tmp_out/defaultstudy/Displacement fitness (3x3)/
algorithms/tmp_out/defaultstudy/Reward & penalty fitness (3x3)/
algorithms/tmp_out/defaultstudy/thesis_2x2_100gen/
algorithms/tmp_out/defaultstudy/thesis_4x4_100gen/
visuals/videos/2x2/
visuals/videos/3x3/
visuals/videos/3x3_baseline/
visuals/videos/4x4/
.ipynb_checkpoints/
```

These folders are older or supporting outputs and are not part of the final thesis analysis.

## Git LFS

This repository uses Git LFS for videos and large output files. After cloning the repository, run:

```bash
git lfs install
git lfs pull
```

## Dependencies

Recommended `requirements.txt`:

```text
numpy
sqlalchemy
matplotlib
scipy
pandas
lxml
opencv-python
scikit-learn
gymnasium
shapely
Pillow
imageio
imageio-ffmpeg
cma
```

The project also requires EvoGym. Install it using the correct local path, for example:

```bash
pip install -e ../evogym --no-deps --no-build-isolation
```

or, if EvoGym is inside this repository:

```bash
pip install -e ./evogym --no-deps --no-build-isolation
```

## Environment Setup

From the repository root:

```bash
python3.9 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then install EvoGym:

```bash
pip install -e ../evogym --no-deps --no-build-isolation
```

## Running Experiments

Run commands from the repository root.

### Displacement-Only Condition

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

### Reward & Penalty Condition

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

Keep experiment names consistent with the analysis scripts. If folder names are changed, update the experiment names inside the analysis scripts.

## Analysis Workflow

Before running analysis scripts, check local path variables such as:

```python
MAINPATH = "..."
PLOTDIR = "..."
```

Typical workflow:

```bash
python analysis/intricacy.py
python analysis/phase_grids.py
python analysis/plots/plot.py
python analysis/plots/5x5_balance/balance.py
```

The analysis scripts generate CSV files, plots, actuator-balance results, morphology visualizations, screenshots, and optional videos.

## Main Thesis Metrics

| Metric | Description |
|---|---|
| Fitness | Selection score used by evolution |
| Displacement | Forward movement in EvoGym |
| Body size | Number of occupied voxels |
| Material composition | Counts and proportions of material types |
| Actuator balance | Balance between phase and off-phase actuators |
| Raw intricacy | Number of right-angle boundary turns |
| Intricacy per voxel | Intricacy normalized by body size |
| Intricacy per perimeter | Intricacy normalized by perimeter |

## Notes

The thesis focuses on the final `5x5` experimental runs. Older `2x2`, `3x3`, and `4x4` outputs were used during development but are not part of the final thesis analysis.

Some scripts may contain local absolute paths and may need manual editing on other machines. The controller is fixed, so the evolving GRN is responsible for the robot morphology and actuator phase offsets. Body size is not directly rewarded by the reward & penalty fitness function. Boundary intricacy measures only the complexity of the external outline. Actuator balance measures only the number of phase and off-phase actuators, not their spatial placement or coordination quality.

## Reproducibility Checklist

1. Create the Python environment.
2. Install the required Python packages.
3. Install EvoGym.
4. Run ten `5x5` displacement-only experiments.
5. Run ten `5x5` reward & penalty experiments.
6. Check and update local paths in the analysis scripts if needed.
7. Run boundary-intricacy analysis.
8. Run actuator-balance analysis.
9. Generate the final plots.
10. Inspect the final evolved robots and videos.
