"""
Same-domain "default" implementations. These are what a competent software
engineer reaches for without looking outside the field. Each one backs a
distractor KnowledgeCard (software_engineering domain) AND is also used as
the Baseline-A "no retrieval, same-domain only" candidate for its problem.

They are deliberately reasonable, real techniques -- not strawmen. The point
of the benchmark is that each one has a genuine, known failure mode that the
matching cross-domain mechanism (in the sibling modules of this package)
avoids.
"""
import random
from collections import Counter

from .predator_prey_damping import make_damped_step, lv_step  # noqa: F401 (re-exported for convenience)


class ThresholdAutoscaler:
    """Bang-bang control: step in a fixed direction whenever a threshold is crossed."""

    def __init__(self, low_mark, high_mark, step=1.0):
        self.low_mark = low_mark
        self.high_mark = high_mark
        self.step_size = step

    def step(self, measured_value, dt=1.0):
        if measured_value > self.high_mark:
            return self.step_size
        if measured_value < self.low_mark:
            return -self.step_size
        return 0.0


def materialize_then_sample(stream, k, seed=None):
    rng = random.Random(seed)
    data = list(stream)  # materializes the entire stream
    if len(data) <= k:
        return data
    return rng.sample(data, k)


class NearestNeighborPolicy:
    """Incremental version: always go to whichever pending request is
    currently closest, re-evaluated after every stop."""

    def next_target(self, pending, pos):
        if not pending:
            return None
        return min(pending, key=lambda r: abs(r - pos))


def nearest_neighbor_dispatch(requests, start):
    remaining = sorted(set(requests))
    pos = start
    order = []
    dist = 0
    while remaining:
        nxt = min(remaining, key=lambda r: abs(r - pos))
        dist += abs(nxt - pos)
        pos = nxt
        order.append(nxt)
        remaining.remove(nxt)
    return order, dist


def first_fit_decreasing(item_sizes, num_bins):
    loads = [0.0] * num_bins
    for size in sorted(item_sizes, reverse=True):
        i = min(range(num_bins), key=lambda b: loads[b])  # least-loaded bin ~ first-fit-decreasing for load balancing
        loads[i] += size
    return loads


def central_fanout_broadcast(all_nodes, origin, alive_mask_fn):
    """Single round, direct push from origin to every node; no relay, no retry."""
    informed = {origin}
    for n in all_nodes:
        if n == origin:
            continue
        if alive_mask_fn(n, 0):
            informed.add(n)
    return informed


def static_shortest_path_choice(initial_costs: dict):
    """Chooses once, from the initial cost snapshot, and never revisits it."""
    return min(initial_costs, key=lambda p: initial_costs[p])


class ZScoreDetector:
    def __init__(self, threshold=3.0):
        self.threshold = threshold
        self.mean = 0.0
        self.std = 1.0

    @staticmethod
    def _feature(sample: str) -> float:
        return float(sample.count("1"))

    def train(self, normal_samples):
        feats = [self._feature(s) for s in normal_samples]
        n = len(feats)
        self.mean = sum(feats) / n
        var = sum((f - self.mean) ** 2 for f in feats) / n
        self.std = max(var ** 0.5, 1e-9)

    def is_anomalous(self, sample):
        z = abs(self._feature(sample) - self.mean) / self.std
        return z > self.threshold


def strict_priority_schedule(arrivals, horizon):
    from .auction_scheduling import auction_schedule
    return auction_schedule(arrivals, horizon, escalation_rate=0.0)


class AdmitAllPolicy:
    """Admits every unit of offered load immediately; no metering at the edge."""

    def tick(self, offered_load):
        return offered_load


def last_write_wins(reports):
    return sorted(reports, key=lambda r: r[1])[-1][0]


def undamped_scaling_step(prey, predator):
    return make_damped_step(0.0)(prey, predator)


def no_rebalancing(loads, neighbors_fn=None, rounds=None):
    return dict(loads)


def linear_scan(sorted_list, target):
    comparisons = 0
    for i, v in enumerate(sorted_list):
        comparisons += 1
        if v == target:
            return i, comparisons
    return -1, comparisons
