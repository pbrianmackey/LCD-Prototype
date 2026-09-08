"""
Problem: warehouse_robot_picking
Donor mechanism: logistics_elevator_scan (cross-domain: operations research / elevator scheduling)
Same-domain distractor / Baseline A: se_nearest_neighbor_dispatch

A picking robot on a single long aisle must visit a fixed set of pick
locations (given as signed distances in feet from the dock at 0) minimizing
total travel. The locations form the classical adversarial construction for
"always go to the nearest unvisited request" on a line (alternating sides,
geometrically increasing distance), which forces repeated backtracking;
sweeping in one direction before reversing (SCAN) is provably within a
bounded factor of optimal on a line and comfortably beats nearest-neighbor
on this instance.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lcd.mechanisms.scan_scheduling import ScanPolicy
from lcd.mechanisms.naive_baselines import NearestNeighborPolicy

START = 0
PICK_LOCATIONS = [-643, -198, -61, -19, -6, -2, 1, 3, 10, 34, 110, 357]
PASS_DISTANCE_THRESHOLD = 1700  # calibrated: SCAN=1357ft, nearest-neighbor=1907ft (see __main__)


def _run(policy):
    pos = START
    pending = set(PICK_LOCATIONS)
    total_dist = 0
    stops = 0
    while pending:
        target = policy.next_target(pending, pos)
        if target is None:
            break
        total_dist += abs(target - pos)
        pos = target
        pending.discard(target)
        stops += 1
    return total_dist, stops


CARD_ADAPTERS = {
    "logistics_elevator_scan": lambda: ScanPolicy(initial_direction=1),
    "se_nearest_neighbor_dispatch": lambda: NearestNeighborPolicy(),
}


def evaluate(candidate):
    total_dist, stops = _run(candidate)
    passed = total_dist <= PASS_DISTANCE_THRESHOLD
    score = -total_dist
    detail = f"total_distance={total_dist}ft over {stops} stops (limit {PASS_DISTANCE_THRESHOLD}ft)"
    return passed, score, detail


if __name__ == "__main__":
    for name, factory in CARD_ADAPTERS.items():
        c = factory()
        p, s, d = evaluate(c)
        print(name, "PASS" if p else "FAIL", d)
