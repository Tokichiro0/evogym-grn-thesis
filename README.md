# GRN-Developed Soft Robots in EvoGym

This repository contains the code used for my bachelor thesis experiments on evolving 2D soft robots in EvoGym with a Gene Regulatory Network (GRN)-based developmental encoding.

The project builds on an existing EvoGym-GRN codebase. For the thesis, the code was adapted to compare two fitness conditions in a `5x5` voxel design space:

1. displacement-only fitness
2. reward & penalty fitness

The goal is to study whether displacement-based selection favors smaller morphologies, and whether reward shaping can produce larger or more structured robots without significantly reducing locomotion performance.

## Research Question

> Does displacement-based selection in GRN-developed soft robots create pressure toward smaller morphologies, and can reward shaping produce more complex bodies without reducing locomotion performance?

## Repository Structure

```text
evogym-GRN/
├── algorithms/
│   ├── basic_EA_thesis.py
│   ├── GRN_2D.py
│   ├── voxel_types.py
│   ├── EA_classes.py
│   ├── experiment.py
│   └── tmp_out/
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
│   └── plots/
│
├── experiments/
├── visuals/
├── requirements.txt
└── README.md
```

The main thesis code is in:

- `algorithms/`
- `simulation/`
- `utils/`
- `analysis/`

The `experiments/` folder contains older or supporting scripts from the broader project. The `visuals/` folder contains generated screenshots, pictures, and videos.

## Main Adaptations

Compared to the original codebase, this thesis version adds or adapts:

- `algorithms/basic_EA_thesis.py` as the main thesis evolutionary algorithm
- GRN development with actuator phase values
- phase and off-phase actuator types
- conversion from GRN phenotypes to EvoGym robot structures
- EvoGym simulation with a fixed sine-wave controller
- displacement-only fitness
- reward & penalty fitness
- morphology metrics such as body size, material composition, actuator balance, and intricacy
- analysis scripts for plots, actuator balance, and boundary intricacy

The main file for running thesis experiments is:

```text
algorithms/basic_EA_thesis.py
```

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

Main evolutionary algorithm for the thesis experiments. It handles population initialization, selection, crossover, mutation, GRN development, EvoGym simulation, metric calculation, survivor selection, and saving results.

Mutation is applied before development, so the evaluated phenotype belongs to the final mutated genome.

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

Converts a developed GRN phenotype into EvoGym-compatible robot data. It trims empty borders, maps GRN material IDs to EvoGym voxel IDs, creates connectivity, and keeps actuator phase offsets aligned with the robot body.

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

Redevelops saved genomes from the experiment databases and calculates boundary-based morphology metrics:

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

## Generated Outputs

### `algorithms/tmp_out/`

Stores raw evolutionary run outputs.

Example structure:

```text
algorithms/tmp_out/
└── defaultstudy/
    ├── Displacement fitness (5×5)/
    │   ├── run_1/
    │   └── ...
    └── Reward & penalty fitness (5×5)/
        ├── run_1/
        └── ...
```

Each run folder contains an SQLite database with saved robots, genomes, fitness values, displacement values, and generation-survivor information.

### `analysis/intricacy_per_gen_final.csv`

CSV file containing post-hoc metrics used for final plots and comparisons.

Typical columns include:

- experiment
- run
- generation
- robot ID
- fitness
- displacement
- number of voxels
- intricacy
- perimeter
- intricacy per voxel
- intricacy per perimeter

### `visuals/pictures/`

Contains screenshots and static robot images for visual inspection.

### `visuals/videos/`

Contains generated robot videos. These are useful for presentation but are not required for the numerical analysis.

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

### Displacement-only condition

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

### Reward & penalty condition

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

Before running analysis scripts, check path variables such as:

```python
MAINPATH = "..."
PLOTDIR = "..."
```

Typical workflow:

```bash
python analysis/intricacy.py
python analysis/phase_grids.py
python analysis/plots/plot.py
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

- The final thesis focuses on the `5x5` experiments.
- Some older scripts in `experiments/` are kept for reference.
- Some analysis scripts may still contain older `3x3` settings.
- Some scripts contain local absolute paths and may need to be edited on another machine.
- The controller is fixed; the GRN evolves morphology and actuator phase offsets.
- The reward & penalty fitness does not directly reward body size.
- Boundary intricacy measures only external outline complexity.
- Generated outputs such as `tmp_out/`, plots, screenshots, and videos are not core source code.

## Recommended `.gitignore`

```gitignore
__pycache__/
*.pyc
.ipynb_checkpoints/

# Evolution output
algorithms/tmp_out/

# Databases
*.sqlite
*.db

# Videos
*.mp4
*.avi
visuals/videos/
```

## Reproducibility Checklist

1. Set up the Python environment.
2. Install the required packages.
3. Install EvoGym.
4. Run 10 displacement-only `5x5` experiments.
5. Run 10 reward & penalty `5x5` experiments.
6. Update paths in the analysis scripts.
7. Run intricacy analysis.
8. Run actuator-balance analysis.
9. Generate final plots.
10. Use final-generation data for statistical tests.