"""
Problem: replication_broadcast
Donor mechanism: epidemiology_sir_gossip (cross-domain: epidemiology)
Same-domain distractor / Baseline A: se_central_fanout_broadcast

Propagate a write from one origin node to as much of a 40-node ring-lattice
network as possible (each node connected to its 4 nearest ring neighbors --
not a complete graph, so most node pairs are not directly connected), where
any node has a 25% chance of being unreachable/non-relaying in any given
round. Central fan-out only ever reaches the origin's 4 direct neighbors and
never anyone further away. Epidemic-style relaying over several rounds
reaches nearly everyone despite the same per-round failure rate, because
nodes that fail to relay in one round get more chances in later rounds via
other paths (15 rounds, fan-out 4, is enough to reach ~100% here).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import random

from lcd.mechanisms.epidemic_broadcast import epidemic_broadcast
from lcd.mechanisms.naive_baselines import central_fanout_broadcast

N = 40
ORIGIN = 0
ROUNDS = 15
FANOUT = 4
FAILURE_PROB = 0.25
PASS_COVERAGE_THRESHOLD = 0.85


def _neighbors(node):
    return sorted({(node + d) % N for d in (-2, -1, 1, 2)})


def _alive_mask_factory(seed):
    rng = random.Random(seed)
    cache = {}

    def alive(node, rnd):
        key = (node, rnd)
        if key not in cache:
            cache[key] = rng.random() > FAILURE_PROB
        return cache[key]
    return alive


def _epidemic_candidate():
    def solve():
        alive = _alive_mask_factory(seed=7)
        return epidemic_broadcast(_neighbors, ORIGIN, ROUNDS, FANOUT, alive, seed=7)
    return solve


def _central_fanout_candidate():
    def solve():
        alive = _alive_mask_factory(seed=7)
        # naive: origin pushes directly to its own graph neighbors only, one round, no relay
        return central_fanout_broadcast(_neighbors(ORIGIN) + [ORIGIN], ORIGIN, alive)
    return solve


CARD_ADAPTERS = {
    "epidemiology_sir_gossip": _epidemic_candidate,
    "se_central_fanout_broadcast": _central_fanout_candidate,
}


def evaluate(candidate):
    informed = candidate()
    coverage = len(informed) / N
    passed = coverage >= PASS_COVERAGE_THRESHOLD
    score = coverage
    detail = f"coverage={coverage:.2%} ({len(informed)}/{N} nodes), limit {PASS_COVERAGE_THRESHOLD:.0%}"
    return passed, score, detail


if __name__ == "__main__":
    for name, factory in CARD_ADAPTERS.items():
        c = factory()
        p, s, d = evaluate(c)
        print(name, "PASS" if p else "FAIL", d)
