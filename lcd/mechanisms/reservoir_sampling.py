"""Reservoir sampling, Algorithm R (donor mechanism: statistics_reservoir_sampling).

Single pass, O(k) memory regardless of stream length. Never materializes the
input beyond the k-slot reservoir.
"""
import random


def reservoir_sample(stream, k, seed=None):
    rng = random.Random(seed)
    reservoir = []
    for i, item in enumerate(stream):
        if i < k:
            reservoir.append(item)
        else:
            j = rng.randint(0, i)
            if j < k:
                reservoir[j] = item
    return reservoir
