"""
Problem: anomaly_detection_no_labels
Donor mechanism: immunology_negative_selection (cross-domain: immunology)
Same-domain distractor / Baseline A: se_zscore_outlier

Only "normal" examples are available (no labeled anomalies). Normal system
states are 16-bit patterns with 2-4 active bits, always confined to the left
half (positions 0-7). Evaluation anomalies also have 2-4 active bits (so the
active-bit COUNT distribution is identical between normal and anomalous --
a single numeric summary statistic like "count of active bits" has zero
discriminating power, by construction) but theirs are confined to the right
half (positions 8-15): a structural/positional difference invisible to any
detector that reduces the pattern to one count.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lcd.mechanisms.negative_selection import NegativeSelectionDetector
from lcd.mechanisms.naive_baselines import ZScoreDetector

LENGTH = 16
LEFT_POSITIONS = list(range(0, 8))
RIGHT_POSITIONS = list(range(8, 16))
ACTIVE_BIT_CHOICES = [2, 3, 4]
N_TRAIN, N_HELD_OUT, N_ANOMALY = 300, 200, 200
NEG_SELECTION_R = 5
PASS_DETECTION_RATE = 0.9
MAX_FALSE_POSITIVE_RATE = 0.2


def _rand_pattern(positions, k, rng):
    chosen = rng.sample(positions, k)
    s = ["0"] * LENGTH
    for p in chosen:
        s[p] = "1"
    return "".join(s)


def _sample_set(positions, n, rng):
    return [_rand_pattern(positions, rng.choice(ACTIVE_BIT_CHOICES), rng) for _ in range(n)]


def _datasets():
    rng = random.Random(11)
    train = _sample_set(LEFT_POSITIONS, N_TRAIN, rng)
    held_out = _sample_set(LEFT_POSITIONS, N_HELD_OUT, rng)
    anomalies = _sample_set(RIGHT_POSITIONS, N_ANOMALY, rng)
    return train, held_out, anomalies


def _negative_selection_candidate():
    def solve():
        train, held_out, anomalies = _datasets()
        det = NegativeSelectionDetector(length=LENGTH, alphabet="01", r=NEG_SELECTION_R,
                                         num_detectors=300, seed=5)
        det.train(train, max_attempts_factor=400)
        detected = sum(1 for a in anomalies if det.is_anomalous(a))
        false_pos = sum(1 for n in held_out if det.is_anomalous(n))
        return detected / len(anomalies), false_pos / len(held_out)
    return solve


def _zscore_candidate():
    def solve():
        train, held_out, anomalies = _datasets()
        det = ZScoreDetector(threshold=2.0)
        det.train(train)
        detected = sum(1 for a in anomalies if det.is_anomalous(a))
        false_pos = sum(1 for n in held_out if det.is_anomalous(n))
        return detected / len(anomalies), false_pos / len(held_out)
    return solve


CARD_ADAPTERS = {
    "immunology_negative_selection": _negative_selection_candidate,
    "se_zscore_outlier": _zscore_candidate,
}


def evaluate(candidate):
    detection_rate, false_pos_rate = candidate()
    passed = bool(detection_rate >= PASS_DETECTION_RATE and false_pos_rate <= MAX_FALSE_POSITIVE_RATE)
    score = detection_rate - false_pos_rate
    detail = (f"detection_rate={detection_rate:.2%} (need >={PASS_DETECTION_RATE:.0%}), "
              f"false_positive_rate={false_pos_rate:.2%} (need <={MAX_FALSE_POSITIVE_RATE:.0%})")
    return passed, score, detail


if __name__ == "__main__":
    for name, factory in CARD_ADAPTERS.items():
        c = factory()
        p, s, d = evaluate(c)
        print(name, "PASS" if p else "FAIL", d)
