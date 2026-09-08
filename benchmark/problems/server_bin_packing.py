"""
Problem: server_bin_packing
Donor mechanism: statistical_physics_simulated_annealing (cross-domain: statistical physics)
Same-domain distractor / Baseline A: se_first_fit_decreasing

Assign fixed-cost jobs to a fixed number of servers to minimize the maximum
load (makespan). The instance below is a verified, brute-force-confirmed
case where the standard greedy heuristic (sort jobs largest-first, place
each on the currently least-loaded server -- "LPT") lands on makespan 20
while the true optimum is 17: LPT has no way to look ahead and see that
holding two mid-size jobs together briefly overloads one machine relative to
the globally best partition. Simulated annealing, which searches the
assignment space directly rather than committing greedily, finds 17-18
across random seeds (see calibrate.py for the brute-force verification).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lcd.mechanisms.simulated_annealing import anneal
from lcd.mechanisms.naive_baselines import first_fit_decreasing

ITEMS = [6, 5, 9, 7, 9, 8, 6]
NUM_BINS = 3
OPTIMAL_MAKESPAN = 17  # brute-force verified over all 3^7 assignments
PASS_MAKESPAN_THRESHOLD = 18  # LPT achieves 20 on this instance; optimal is 17


def _loads_for_assignment(assignment):
    loads = [0.0] * NUM_BINS
    for x, b in zip(ITEMS, assignment):
        loads[b] += x
    return loads


def _sa_candidate():
    def cost_fn(assignment):
        return max(_loads_for_assignment(assignment))

    def neighbor_fn(assignment, rng):
        new = list(assignment)
        i = rng.randrange(len(ITEMS))
        new[i] = rng.randrange(NUM_BINS)
        return new

    def solve():
        init = [0] * len(ITEMS)
        best, _best_cost = anneal(init, neighbor_fn, cost_fn, iterations=4000,
                                   initial_temp=8.0, cooling=0.995, seed=42)
        return _loads_for_assignment(best)
    return solve


def _ffd_candidate():
    def solve():
        return first_fit_decreasing(ITEMS, NUM_BINS)
    return solve


CARD_ADAPTERS = {
    "statistical_physics_simulated_annealing": _sa_candidate,
    "se_first_fit_decreasing": _ffd_candidate,
}


def evaluate(candidate):
    loads = candidate()
    valid = abs(sum(loads) - sum(ITEMS)) < 1e-6 and len(loads) == NUM_BINS
    makespan = max(loads) if valid else float("inf")
    passed = bool(valid and makespan <= PASS_MAKESPAN_THRESHOLD)
    score = -makespan
    detail = f"makespan={makespan} (optimal={OPTIMAL_MAKESPAN}, limit {PASS_MAKESPAN_THRESHOLD}), loads={loads}"
    return passed, score, detail


if __name__ == "__main__":
    for name, factory in CARD_ADAPTERS.items():
        c = factory()
        p, s, d = evaluate(c)
        print(name, "PASS" if p else "FAIL", d)
