"""
Problem: producer_consumer_oscillation
Donor mechanism: ecology_predator_prey_damping (cross-domain: ecology)
Same-domain distractor / Baseline A: se_reactive_worker_step

A backlog (prey) and a worker pool (predator) interact multiplicatively:
workers grow in proportion to backlog*workers, backlog shrinks in proportion
to the same product, and backlog has its own base growth rate -- a discrete
Lotka-Volterra pair. Purely reactive scaling with no self-limiting term
produces sustained, large boom-bust oscillation (classic predator-prey
cycling). Adding a capacity-limiting (carrying-capacity) term to the worker
growth rule damps the system to a stable equilibrium.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import statistics

from lcd.mechanisms.predator_prey_damping import make_damped_step

STEPS = 2000
DT = 0.05
INITIAL_PREY, INITIAL_PREDATOR = 15.0, 10.0
PASS_AMPLITUDE_THRESHOLD = 5.0


def _simulate(step_fn):
    prey, predator = INITIAL_PREY, INITIAL_PREDATOR
    tail = []
    tail_start = int(STEPS * 0.8)
    for i in range(STEPS):
        prey, predator = step_fn(prey, predator)
        if i >= tail_start:
            tail.append(predator)
    return tail


def _damped_candidate():
    return make_damped_step(e_damping=0.03, a=1.0, b=0.1, c=1.0, d=0.1, dt=DT)


def _undamped_candidate():
    # same a,b,c,d,dt as the damped candidate -- e_damping is the only difference,
    # exactly like naive_baselines.undamped_scaling_step but with matched dt.
    return make_damped_step(e_damping=0.0, a=1.0, b=0.1, c=1.0, d=0.1, dt=DT)


CARD_ADAPTERS = {
    "ecology_predator_prey_damping": _damped_candidate,
    "se_reactive_worker_step": _undamped_candidate,
}


def evaluate(candidate):
    tail = _simulate(candidate)
    amplitude = max(tail) - min(tail)
    passed = amplitude <= PASS_AMPLITUDE_THRESHOLD
    score = -amplitude
    detail = f"late_stage_amplitude={amplitude:.2f} (limit {PASS_AMPLITUDE_THRESHOLD}), stdev={statistics.pstdev(tail):.2f}"
    return passed, score, detail


if __name__ == "__main__":
    for name, factory in CARD_ADAPTERS.items():
        c = factory()
        p, s, d = evaluate(c)
        print(name, "PASS" if p else "FAIL", d)
