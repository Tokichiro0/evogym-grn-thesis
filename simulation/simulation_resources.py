#!/usr/bin/env python3
import math
from typing import Dict, List, Tuple
import numpy as np

def _resolve_steps(args) -> int:
    steps = int(getattr(args, "evogym_steps", 500))
    return max(1, steps)

def _simulate_one_robot(task: Dict) -> Tuple[int, float, str]:
    import gymnasium as gym
    import evogym.envs

    robot_id = int(task["id"])

    try:
        render_mode = "human" if int(task.get("headless", 1)) == 0 else None

        env = gym.make(
            "Walker-v0",
            body=task["structure"],
            connections=task["connections"],
            render_mode=render_mode,
        )
        env.reset()
        sim = env.unwrapped.sim

        actuator_indices = sim.get_actuator_indices("robot").astype(int).flatten()
        phase_flat = task["phase_offsets"].reshape(-1)
        actuator_phases = phase_flat[actuator_indices] if actuator_indices.size else np.array([])

        x0 = float(np.mean(sim.object_pos_at_time(sim.get_time(), "robot")[0]))

        bias = float(task["action_bias"])
        amplitude = float(task["action_amplitude"])
        period_steps = max(1, int(task["period_steps"]))

        for t in range(int(task["sim_steps"])):
            if actuator_indices.size:
                angle = 2.0 * math.pi * (t / period_steps)
                action = np.clip(
                    bias + amplitude * np.sin(angle + actuator_phases),
                    0.6,
                    1.6,
                ).astype(np.float64)
                env.step(action)
            else:
                env.step(np.array([]))

        x1 = float(np.mean(sim.object_pos_at_time(sim.get_time(), "robot")[0]))
        env.close()

        return robot_id, max(0.0, x1 - x0), ""

    except Exception as exc:
        return robot_id, float("-inf"), f"{type(exc).__name__}: {exc}"

def simulate_evogym_batch(population, args):
    sim_steps = _resolve_steps(args)
    default_bias = float(getattr(args, "evogym_action_bias", 1.0))
    default_amplitude = float(getattr(args, "evogym_action_amplitude", 0.4))
    default_period = int(getattr(args, "evogym_period_steps", 20))
    headless = int(getattr(args, "evogym_headless", 1))

    id_to_ind = {ind.id: ind for ind in population}
    tasks: List[Dict] = []

    for ind in population:
        if not getattr(ind, "valid", True):
            continue

        if not hasattr(ind, "evogym_structure") or ind.evogym_structure is None:
            ind.displacement = float("-inf")
            continue

        n_actuators = int(np.sum(ind.evogym_structure == 3))
        if n_actuators < 2:
            ind.displacement = float("-inf")
            continue

        if ind.evogym_structure.shape[0] < 2 or ind.evogym_structure.shape[1] < 2:
            ind.displacement = float("-inf")
            continue

        ctrl = getattr(ind, "evogym_controller", {})
        task = {
            "id": ind.id,
            "structure": ind.evogym_structure,
            "connections": ind.evogym_connections,
            "phase_offsets": ind.evogym_phase_offsets,
            "action_bias": ctrl.get("action_bias", default_bias),
            "action_amplitude": ctrl.get("action_amplitude", default_amplitude),
            "period_steps": ctrl.get("period_steps", default_period),
            "sim_steps": sim_steps,
            "headless": headless,
        }
        tasks.append(task)

    if not tasks:
        print("[SIM-DONE] total=0 ok=0 failed=0")
        return

    ok = 0
    failed = 0

    for task in tasks:
        rid, disp, err = _simulate_one_robot(task)
        ind = id_to_ind[rid]
        ind.displacement = float(disp)

        if err:
            failed += 1
            print(f"[SIM-FAIL] {rid}: {err}", flush=True)
        else:
            ok += 1
    print(f"[SIM-DONE] total={len(tasks)} ok={ok} failed={failed} steps={sim_steps}")