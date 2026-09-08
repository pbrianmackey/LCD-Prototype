"""
Problem: naive_sufficient_lookup   [control_type = naive_sufficient]
Donor mechanism: cs_binary_search -- SAME-DOMAIN, standard CS knowledge
Baseline A: cs_binary_search too (baseline A is *expected* to already succeed here)
Same-domain distractor: se_linear_scan

Look up several targets in a large sorted, static configuration list with a
tight comparison budget. This control checks that the system does not need,
and is not penalized for not finding, a cross-domain mechanism when the
field already has a perfectly good answer (binary search). Nothing here
requires reaching outside software/CS knowledge.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import random

from lcd.mechanisms.binary_search import binary_search
from lcd.mechanisms.naive_baselines import linear_scan

N = 100_000
MAX_AVG_COMPARISONS = 25  # log2(100000) ~ 16.6; linear scan averages ~50,000


def _targets():
    rng = random.Random(3)
    present = rng.sample(range(N), 20)
    absent = [N + i for i in range(10)]  # guaranteed not present
    return present + absent


CARD_ADAPTERS = {
    "cs_binary_search": lambda: binary_search,
    "se_linear_scan": lambda: linear_scan,
}


def evaluate(candidate):
    data = list(range(N))
    total_comparisons = 0
    correct = 0
    targets = _targets()
    for t in targets:
        idx, comparisons = candidate(data, t)
        total_comparisons += comparisons
        expected_idx = t if 0 <= t < N else -1
        if idx == expected_idx:
            correct += 1
    avg_comparisons = total_comparisons / len(targets)
    all_correct = correct == len(targets)
    passed = bool(all_correct and avg_comparisons <= MAX_AVG_COMPARISONS)
    score = -avg_comparisons
    detail = f"avg_comparisons={avg_comparisons:.1f} (limit {MAX_AVG_COMPARISONS}), correct={correct}/{len(targets)}"
    return passed, score, detail


if __name__ == "__main__":
    for name, factory in CARD_ADAPTERS.items():
        c = factory()
        p, s, d = evaluate(c)
        print(name, "PASS" if p else "FAIL", d)
