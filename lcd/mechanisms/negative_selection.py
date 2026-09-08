"""Immune negative selection (donor mechanism: immunology_negative_selection).

Trains detectors that do NOT match any normal example, then flags anything a
surviving detector matches -- works from "normal" examples alone, no labeled
anomalies required, and can catch structural anomalies invisible to a single
numeric summary statistic.
"""
import random


def hamming(a, b):
    return sum(1 for x, y in zip(a, b) if x != y)


class NegativeSelectionDetector:
    def __init__(self, length, alphabet="01", r=3, num_detectors=400, seed=None):
        self.length = length
        self.alphabet = list(alphabet)
        self.r = r
        self.num_detectors = num_detectors
        self.rng = random.Random(seed)
        self.detectors = []

    def train(self, normal_samples, max_attempts_factor=200):
        attempts = 0
        max_attempts = self.num_detectors * max_attempts_factor
        while len(self.detectors) < self.num_detectors and attempts < max_attempts:
            attempts += 1
            cand = "".join(self.rng.choice(self.alphabet) for _ in range(self.length))
            if all(hamming(cand, s) >= self.r for s in normal_samples):
                self.detectors.append(cand)

    def is_anomalous(self, sample):
        return any(hamming(sample, d) < self.r for d in self.detectors)
