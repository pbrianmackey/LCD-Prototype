"""
Problem: starvation_free_scheduling
Donor mechanism: economics_congestion_pricing_aging (cross-domain: economics)
Same-domain distractor / Baseline A: se_strict_priority_queue

One important task (value 3) arrives at tick 0 into a system that also
receives a continuous flood of routine tasks (value 5) at one per tick,
forever, with capacity to serve exactly one task per tick. Under a fixed
(static) priority rule the important task is starved forever -- there is
always a fresh routine task with higher static value. Letting effective bid
grow with wait time (aging / congestion pricing) guarantees it gets served
within a bounded number of ticks.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lcd.mechanisms.auction_scheduling import auction_schedule
from lcd.mechanisms.naive_baselines import strict_priority_schedule

HORIZON = 300
IMPORTANT_VALUE = 3
FLOOD_VALUE = 5
PASS_WAIT_THRESHOLD = 50


def _arrivals():
    arrivals = [(0, "important", IMPORTANT_VALUE)]
    for t in range(HORIZON):
        arrivals.append((t, f"flood_{t}", FLOOD_VALUE))
    return arrivals


def _auction_candidate():
    def solve():
        return auction_schedule(_arrivals(), HORIZON, escalation_rate=0.5)
    return solve


def _strict_priority_candidate():
    def solve():
        return strict_priority_schedule(_arrivals(), HORIZON)
    return solve


CARD_ADAPTERS = {
    "economics_congestion_pricing_aging": _auction_candidate,
    "se_strict_priority_queue": _strict_priority_candidate,
}


def evaluate(candidate):
    served = candidate()
    served_tick = served.get("important")
    if served_tick is None:
        wait = float("inf")
    else:
        wait = served_tick - 0
    passed = wait <= PASS_WAIT_THRESHOLD
    score = -wait if wait != float("inf") else -HORIZON * 10
    detail = f"important_task_wait={wait} ticks (limit {PASS_WAIT_THRESHOLD}), served_tick={served_tick}"
    return passed, score, detail


if __name__ == "__main__":
    for name, factory in CARD_ADAPTERS.items():
        c = factory()
        p, s, d = evaluate(c)
        print(name, "PASS" if p else "FAIL", d)
