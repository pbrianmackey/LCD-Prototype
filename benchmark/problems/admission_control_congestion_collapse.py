"""
Problem: admission_control_congestion_collapse
Donor mechanism: transportation_ramp_metering (cross-domain: transportation engineering)
Same-domain distractor / Baseline A: se_admit_all_retry

A backend can sustainably process 10 units/tick. A 30-tick overload spike
(40 units/tick offered) hits it. Beyond capacity, contention overhead makes
completed throughput fall as admitted concurrency rises past capacity (a
capacity-drop / thrashing model: completed = max(0, S - k*(admitted-S))).
Admitting everything immediately drives completed throughput to zero for
the whole spike (thrashing collapse: 0 completed while overloaded, vs. 8-10
achievable). Metering admission to match capacity and queuing the rest at
the edge keeps completed throughput at capacity the entire time, at the
cost of a temporary queue that drains once the spike ends.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lcd.mechanisms.ramp_metering import RampMeteringAdmission
from lcd.mechanisms.naive_baselines import AdmitAllPolicy

TICKS = 150
SERVICE_RATE = 10
THRASH_K = 1.5
PASS_TOTAL_COMPLETED_THRESHOLD = 1300  # admit-all totals ~960; metering totals ~1500


def _offered_load(t):
    return 40 if 20 <= t < 50 else 8


def _completed(admitted):
    excess = max(0, admitted - SERVICE_RATE)
    base = min(admitted, SERVICE_RATE)  # can't complete more than was admitted
    return max(0.0, base - THRASH_K * excess)


def _run(policy):
    total_completed = 0.0
    for t in range(TICKS):
        admitted = policy.tick(_offered_load(t))
        total_completed += _completed(admitted)
    return total_completed


CARD_ADAPTERS = {
    "transportation_ramp_metering": lambda: RampMeteringAdmission(service_rate=SERVICE_RATE),
    "se_admit_all_retry": lambda: AdmitAllPolicy(),
}


def evaluate(candidate):
    total_completed = _run(candidate)
    passed = total_completed >= PASS_TOTAL_COMPLETED_THRESHOLD
    score = total_completed
    detail = f"total_completed={total_completed:.1f} over {TICKS} ticks (need >={PASS_TOTAL_COMPLETED_THRESHOLD})"
    return passed, score, detail


if __name__ == "__main__":
    for name, factory in CARD_ADAPTERS.items():
        c = factory()
        p, s, d = evaluate(c)
        print(name, "PASS" if p else "FAIL", d)
