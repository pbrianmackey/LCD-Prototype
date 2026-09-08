"""
Problem: adaptive_routing
Donor mechanism: entomology_ant_colony (cross-domain: entomology / stigmergy)
Same-domain distractor / Baseline A: se_static_shortest_path

Three candidate routes between the same source and destination have costs
that shift partway through a long run of repeated trips (a previously-cheap
route becomes congested; a previously-expensive one becomes cheap).
A route computed once from the initial snapshot and cached forever keeps
using the now-congested route. Reinforcement/evaporation-based routing
(pheromone trail update after every trip) drifts toward the new best route
within the remaining trips.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lcd.mechanisms.ant_colony_routing import AntColonyRouter
from lcd.mechanisms.naive_baselines import static_shortest_path_choice

PATHS = ["A", "B", "C"]
INITIAL_COSTS = {"A": 5.0, "B": 8.0, "C": 12.0}
SHIFTED_COSTS = {"A": 20.0, "B": 4.0, "C": 12.0}
SHIFT_AT_TRIP = 100
TOTAL_TRIPS = 200
MEASURE_LAST_N = 50
PASS_AVG_COST_THRESHOLD = 8.0


def _cost(path, trip):
    costs = INITIAL_COSTS if trip < SHIFT_AT_TRIP else SHIFTED_COSTS
    return costs[path]


def _ant_colony_candidate():
    def solve():
        router = AntColonyRouter(PATHS, evaporation=0.2, alpha=1.0, seed=3)
        history = []
        for trip in range(TOTAL_TRIPS):
            path = router.choose()
            cost = _cost(path, trip)
            router.update(path, cost)
            history.append(cost)
        return history
    return solve


def _static_candidate():
    def solve():
        chosen = static_shortest_path_choice(INITIAL_COSTS)
        history = [_cost(chosen, trip) for trip in range(TOTAL_TRIPS)]
        return history
    return solve


CARD_ADAPTERS = {
    "entomology_ant_colony": _ant_colony_candidate,
    "se_static_shortest_path": _static_candidate,
}


def evaluate(candidate):
    history = candidate()
    tail = history[-MEASURE_LAST_N:]
    avg_cost = sum(tail) / len(tail)
    passed = avg_cost <= PASS_AVG_COST_THRESHOLD
    score = -avg_cost
    detail = f"avg_cost_last_{MEASURE_LAST_N}_trips={avg_cost:.2f} (limit {PASS_AVG_COST_THRESHOLD})"
    return passed, score, detail


if __name__ == "__main__":
    for name, factory in CARD_ADAPTERS.items():
        c = factory()
        p, s, d = evaluate(c)
        print(name, "PASS" if p else "FAIL", d)
