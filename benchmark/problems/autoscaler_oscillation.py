"""
Problem: autoscaler_oscillation
Donor mechanism: control_theory_pid (cross-domain: control theory)
Same-domain distractor / Baseline A: se_threshold_autoscaling

A worker pool must track a target backlog length despite a scripted load
spike, with a one-tick actuation lag between a capacity decision and its
effect on the backlog. Bang-bang (threshold) control overshoots and
oscillates under this lag; a PID controller damps it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lcd.mechanisms.pid import PIDController
from lcd.mechanisms.naive_baselines import ThresholdAutoscaler

TARGET = 10
MIN_WORKERS, MAX_WORKERS = 2, 40
TICKS = 100


def _arrivals():
    # baseline load, then a sustained step spike, then back to baseline
    out = []
    for t in range(TICKS):
        if 30 <= t < 55:
            out.append(24)
        else:
            out.append(10)
    return out


def _simulate(controller_step_fn):
    arrivals = _arrivals()
    queue = TARGET
    workers = TARGET
    history = []
    for t in range(TICKS):
        delta = controller_step_fn(queue)
        workers = min(MAX_WORKERS, max(MIN_WORKERS, workers + delta))
        queue = max(0, queue + arrivals[t] - workers)
        history.append(queue)
    return history


def _mae(history):
    return sum(abs(q - TARGET) for q in history) / len(history)


# ---- candidate factories -------------------------------------------------

def _pid_candidate():
    # Increasing workers *reduces* queue length, so this is a reverse-acting
    # control loop: standard PID practice for a reverse-acting process is
    # negative gains (error = setpoint - measured, output = Kp*error + ...
    # with Kp<0), not a change to the controller's structure.
    return PIDController(kp=-0.9, ki=-0.2, kd=-0.6, setpoint=TARGET,
                          output_limits=(-15, 15), integral_limits=(-20, 20))


def _threshold_candidate():
    return ThresholdAutoscaler(low_mark=TARGET - 2, high_mark=TARGET + 2, step=2)


CARD_ADAPTERS = {
    "control_theory_pid": _pid_candidate,
    "se_threshold_autoscaling": _threshold_candidate,
}

PASS_MAE_THRESHOLD = 6.5  # calibrated: threshold-controller MAE ~ >8-9, PID MAE ~ <5 (see calibrate.py)


def evaluate(candidate):
    history = _simulate(lambda q: candidate.step(q))
    mae = _mae(history)
    passed = mae <= PASS_MAE_THRESHOLD
    score = -mae  # higher (less negative) is better
    detail = f"MAE={mae:.2f} vs threshold {PASS_MAE_THRESHOLD} (queue history sample: {history[28:40]})"
    return passed, score, detail


if __name__ == "__main__":
    for name, factory in [("PID", _pid_candidate), ("Threshold", _threshold_candidate)]:
        c = factory()
        p, s, d = evaluate(c)
        print(name, "PASS" if p else "FAIL", d)
