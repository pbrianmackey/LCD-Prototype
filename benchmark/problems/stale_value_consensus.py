"""
Problem: stale_value_consensus
Donor mechanism: social_choice_quorum_voting (cross-domain: social choice theory)
Same-domain distractor / Baseline A: se_last_write_wins

Five replicas report a value for the same key: three hold the correct,
majority value with older timestamps; two hold a stale minority value but,
because of network delay, carry newer timestamps. Twenty random scenario
instances (values/timestamps randomized, majority/minority roles fixed) are
generated. Last-write-wins always picks the most recent timestamp, which by
construction here is always the wrong (minority/stale) value. Majority
quorum always correctly identifies the value 3 of 5 replicas hold.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lcd.mechanisms.quorum_consensus import quorum_resolve
from lcd.mechanisms.naive_baselines import last_write_wins

NUM_SCENARIOS = 20
PASS_ACCURACY_THRESHOLD = 0.9


def _scenarios():
    scenarios = []
    for seed in range(NUM_SCENARIOS):
        rng = random.Random(seed)
        majority_value, minority_value = "A", "B"
        reports = []
        for _ in range(3):
            reports.append((majority_value, rng.uniform(0, 5)))
        for _ in range(2):
            reports.append((minority_value, rng.uniform(10, 15)))  # stale value, later timestamp
        rng.shuffle(reports)
        scenarios.append((reports, majority_value))
    return scenarios


CARD_ADAPTERS = {
    "social_choice_quorum_voting": lambda: quorum_resolve,
    "se_last_write_wins": lambda: last_write_wins,
}


def evaluate(candidate):
    scenarios = _scenarios()
    correct = sum(1 for reports, truth in scenarios if candidate(reports) == truth)
    accuracy = correct / len(scenarios)
    passed = accuracy >= PASS_ACCURACY_THRESHOLD
    score = accuracy
    detail = f"accuracy={accuracy:.0%} ({correct}/{len(scenarios)} scenarios), need >={PASS_ACCURACY_THRESHOLD:.0%}"
    return passed, score, detail


if __name__ == "__main__":
    for name, factory in CARD_ADAPTERS.items():
        c = factory()
        p, s, d = evaluate(c)
        print(name, "PASS" if p else "FAIL", d)
