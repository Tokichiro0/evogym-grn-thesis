import sys
import numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from evogym import get_full_connectivity

def trim_phenotype_materials(phenotype):
    """
    Trim empty borders from a phenotype and return a 2D grid.
    Also returns the row/col masks used, so we can apply the same trim
    to phase_grid.
    """
    body = np.asarray(phenotype, dtype=int)

    if body.ndim != 2:
        raise ValueError(f"Expected 2D phenotype, got {body.shape}")

    x_mask = np.any(body != 0, axis=1)
    body = body[x_mask]
    y_mask = np.any(body != 0, axis=0)
    body = body[:, y_mask]

    return body, x_mask, y_mask

def _material_maps(voxel_types):
    """
    Map GRN material IDs to EvoGym voxel IDs.
    phase_muscle -> horizontal actuator
    offphase_muscle -> vertical actuator
    """
    EVOGYM = {
        "EMPTY": 0,
        "RIGID": 1,
        "SOFT": 2,
        "H_ACT": 3,
        "V_ACT": 4,
    }
    if voxel_types == "withbone":
        material_to_evogym = {
            0: EVOGYM["EMPTY"],
            1: EVOGYM["RIGID"],
            2: EVOGYM["SOFT"],
            3: EVOGYM["H_ACT"],
            4: EVOGYM["V_ACT"],
        }
    elif voxel_types == "nobone":
        material_to_evogym = {
            0: EVOGYM["EMPTY"],
            1: EVOGYM["SOFT"],
            2: EVOGYM["SOFT"],
            3: EVOGYM["H_ACT"],
            4: EVOGYM["V_ACT"],
        }
    else:
        raise ValueError(f"Unsupported voxel_types: {voxel_types}")

    return material_to_evogym


def _build_evogym_robot_data(body_materials, phase_grid_trimmed, voxel_types):
    material_to_evogym = _material_maps(voxel_types)
    structure = np.vectorize(
        lambda m: material_to_evogym.get(int(m), 0),
        otypes=[int]
    )(body_materials).astype(np.int32)
    connections = get_full_connectivity(structure).astype(np.int32)
    phase_offsets = np.where(
        (body_materials == 3) | (body_materials == 4),
        phase_grid_trimmed,
        0.0
    ).astype(np.float32)

    controller = {
        "action_bias": 1.0,
        "action_amplitude": 0.4,
        "period_steps": 20,
    }
    return structure, connections, phase_offsets, controller

def prepare_robot_files(individual, args):
    """
    Prepare EvoGym robot artifacts from an evolved phenotype.
    Uses the trimmed phase_grid from the individual directly.
    """
    try:
        body, x_mask, y_mask = trim_phenotype_materials(individual.phenotype)

        phase_grid = np.asarray(individual.phase_grid, dtype=float)
        phase_grid_trimmed = phase_grid[x_mask][:, y_mask]

        structure, connections, phase_offsets, controller = _build_evogym_robot_data(
            body, phase_grid_trimmed, args.voxel_types
        )

        individual.evogym_structure = structure
        individual.evogym_connections = connections
        individual.evogym_phase_offsets = phase_offsets
        individual.evogym_controller = controller

    except Exception as e:
        print(f"[PREP-FAIL] id={individual.id}: {e}")
        individual.evogym_structure = None
        individual.evogym_connections = None
        individual.evogym_phase_offsets = None
        individual.evogym_controller = None