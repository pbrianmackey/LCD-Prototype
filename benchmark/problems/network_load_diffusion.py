"""
Problem: network_load_diffusion
Donor mechanism: physics_heat_diffusion (cross-domain: physics)
Same-domain distractor / Baseline A: se_no_rebalancing

One server in a 20-node network starts overloaded (all load on node 0), the
rest idle. Servers can only exchange load with their direct graph neighbors
(no global view, no central coordinator). Repeated local averaging
(discrete heat diffusion) equalizes load across rounds; doing nothing
leaves the extreme imbalance in place forever.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import statistics

from lcd.mechanisms.diffusion_balancing import diffuse_balance
from lcd.mechanisms.naive_baselines import no_rebalancing

N = 20
ROUNDS = 30
ALPHA = 0.15
PASS_STDEV_THRESHOLD = 60.0


def _neighbors(node):
    return sorted({(node + d) % N for d in (-2, -1, 1, 2)})


def _initial_loads():
    loads = {i: 0.0 for i in range(N)}
    loads[0] = 1000.0
    return loads


def _diffusion_candidate():
    def solve():
        return diffuse_balance(_initial_loads(), _neighbors, ROUNDS, alpha=ALPHA)
    return solve


def _no_rebalancing_candidate():
    def solve():
        return no_rebalancing(_initial_loads(), _neighbors, ROUNDS)
    return solve


CARD_ADAPTERS = {
    "physics_heat_diffusion": _diffusion_candidate,
    "se_no_rebalancing": _no_rebalancing_candidate,
}


def evaluate(candidate):
    final_loads = candidate()
    values = list(final_loads.values())
    conserved = abs(sum(values) - 1000.0) < 1e-3
    stdev = statistics.pstdev(values)
    passed = bool(conserved and stdev <= PASS_STDEV_THRESHOLD)
    score = -stdev
    detail = f"stdev={stdev:.1f} (limit {PASS_STDEV_THRESHOLD}), conserved_total={conserved}"
    return passed, score, detail


if __name__ == "__main__":
    for name, factory in CARD_ADAPTERS.items():
        c = factory()
        p, s, d = evaluate(c)
        print(name, "PASS" if p else "FAIL", d)
