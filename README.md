# GRN-Developed Soft Robots in EvoGym

In this repository is the code I wrote for the execution of experiments in my bachelor’s thesis about evolving 2D soft robots using a Gene Regulatory Network (GRN) as a developmental encoding in an EvoGym environment.

This work is based on pre-existing EvoGym-GRN source code. The purpose of my research was to adapt the pre-existing code to assess two different prize and penalty systems within a 5x5 voxel design space.

displacement only fitness
reward & penalty based fitness
The goal of my dissertation project is to investigate the potential for selection based on displacement to produce smaller morphologies, and if using reward shaping could allow for larger or more structured robots without greatly decreasing their ability to locomote.

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
│   └── experiment.py
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
│       ├── plot.py
│       ├── plots_5x5/
│       └── 5x5_balance/
│
├── visuals/
│   └── pictures/
│
├── experiments/
├── requirements.txt
├── .gitignore
└── README.md
```

The main thesis code is in `algorithms/`, `simulation/`, `utils/`, and `analysis/`.

The `experiments/` folder contains older or supporting scripts from the broader original project. The `visuals/pictures/` folder contains example robot screenshots used for inspection and thesis figures.

Raw evolutionary run folders, SQLite databases, and videos are not included in the repository because they are generated outputs and can become large.

## Main Adaptations

In addition to the original EvoGym-GRN library, this version of the Thesis has developed the following systems or made modifications to them:
- `algorithms/basic_EA_thesis.py` as the main thesis evolutionary algorithm
- Development of a GRN with actuator phase values.
- Development of phase and off-phase actuator types
- Development of the ability to convert GRN phenotypes into EvoGym robot structures.
- Provision of an EvoGym simulator using a fixed sine-wave controller.
- Displacement-only fitness
- Reward & penalty fitness
- The creation of Morphology Metrics - for example, body size, materials, actuator balance, intricacy, etc.
- The development of analysis scripts to generate final plots, actuator balance, and boundary intricacy plots.

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

The primary evolutionary algorithm used for the experiments in the thesis performs the following tasks: population initialization, parent selection, crossover, mutation, GRN development, EvoGym simulation, fitness calculation, survivor selection, elitism, and result saving.

Mutations occur before GRN development such that the evaluated phenotype represents the genome that has undergone all the final mutations.

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

Differentiates developed GRN phenotype into compatible robotic data according to EvoGym. Removes empty borders, associates GRN material IDs with EvoGym voxel IDs, establishes connection, and synchronizes actuator phase offsets with robot body position.

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

- Displacement
- Material diversity bonus
- Actuator balance bonus
- Penalty for too few actuators
- Penalty for invalid morphologies

The reward fitness does not directly reward body size.

### `utils/config.py`

Defines command-line arguments such as population size, number of generations, grid size, maximum voxels, fitness metric, run number, and EvoGym controller settings.

## Analysis Scripts

### `analysis/intricacy.py`

Redevelops saved genomes from experiment databases and calculates boundary-based morphology metrics:

- Raw intricacy
- Intricacy per voxel
- Intricacy per perimeter

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

- Fitness over generations
- Displacement over generations
- Body size over generations
- Raw intricacy over generations
- Intricacy per voxel over generations
- Displacement versus intricacy scatter plot

Final plots are saved in:

```text
analysis/plots/plots_5x5/
```

### `analysis/plots/5x5_balance/balance.py`

Generates actuator-balance plots for the final `5x5` experiments.

## Generated Outputs

The repository is mainly intended to store the source code and lightweight final analysis files.

### Included Outputs

The following outputs may be included because they are useful for thesis inspection and reproducibility:

```text
analysis/intricacy_per_gen_final.csv
analysis/plots/plots_5x5/
analysis/plots/5x5_balance/
visuals/pictures/
```

### Not Included Outputs

The following files are generated during experiments and are ignored by Git:

```text
algorithms/tmp_out/
*.sqlite
*.db
visuals/videos/
*.mp4
*.avi
.ipynb_checkpoints/
```

Raw run folders and videos can be regenerated by running the experiments and analysis scripts.

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

The last thesis is a focus on the experimental runs corresponding to Five Experiment Five. Running outputs, data documents and video are purposely not tracked by Git. There are some older versions of the experiment runs kept in experiments/ for reference only. Scripts may also have local absolute paths and so will likely require manual editing on other machines. The controller is fixed and the evolving GRN is responsible for evolution of the resulting morphologies that exist, as well as the evolution of the actuator phase offsets. Body size is not directly rewarded with the reward and penalty fitnesses. The measurement of boundary intricacy is made only on the measures of complexity of the external outline of the objects produced. The measurement of the actuator balance is made solely on the number of actuators employed, and does not take into account either where they are located, or how well their phases are coordinated to one another.

## Reproducibility Checklist

1. Create your Python workspace.
2. Add required modules/library.
3. Add EvoGym module/library.
4. Perform ten 5x5 only-displacement experiments.
5. Perform ten 5x5 both-reward-penalty experiments.
6. Update the analysis scripts to include any required environmental paths.
7. Carry out complexity analysis.
8. Carry out actuator balance analysis.
9. Produce final graphs.
10. Compare finalists to find out who won.
