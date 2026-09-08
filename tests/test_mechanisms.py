"""Sanity tests on the mechanism library itself (independent of any benchmark
problem or retrieval) -- these just check each mechanism does what its
docstring says on a small, direct example."""
import random

from lcd.mechanisms.pid import PIDController
from lcd.mechanisms.reservoir_sampling import reservoir_sample
from lcd.mechanisms.scan_scheduling import scan_schedule, ScanPolicy
from lcd.mechanisms.simulated_annealing import anneal
from lcd.mechanisms.epidemic_broadcast import epidemic_broadcast
from lcd.mechanisms.diffusion_balancing import diffuse_balance
from lcd.mechanisms.auction_scheduling import auction_schedule
from lcd.mechanisms.ant_colony_routing import AntColonyRouter
from lcd.mechanisms.negative_selection import NegativeSelectionDetector, hamming
from lcd.mechanisms.predator_prey_damping import lv_step, make_damped_step
from lcd.mechanisms.ramp_metering import RampMeteringAdmission
from lcd.mechanisms.quorum_consensus import quorum_resolve
from lcd.mechanisms.binary_search import binary_search
from lcd.mechanisms.naive_baselines import (
    ThresholdAutoscaler, materialize_then_sample, NearestNeighborPolicy,
    first_fit_decreasing, central_fanout_broadcast, static_shortest_path_choice,
    ZScoreDetector, strict_priority_schedule, AdmitAllPolicy, last_write_wins,
    no_rebalancing, linear_scan,
)


def test_pid_reduces_error_over_time():
    # Direct-acting toy plant: measured += output (increasing output increases
    # measured), so positive gains are correct here -- the autoscaler problem
    # in benchmark/problems/autoscaler_oscillation.py is reverse-acting
    # (more workers *reduces* the backlog) and correctly uses negative gains;
    # see that file's comment for why the sign is a modeling choice, not a bug.
    pid = PIDController(kp=0.5, ki=0.05, kd=0.05, setpoint=0, output_limits=(-10, 10))
    measured = 10.0
    for _ in range(50):
        measured += pid.step(measured)
    assert abs(measured) < 1.0


def test_reservoir_sample_size_and_membership():
    data = list(range(10_000))
    sample = reservoir_sample(iter(data), 50, seed=1)
    assert len(sample) == 50
    assert len(set(sample)) == 50
    assert all(x in range(10_000) for x in sample)


def test_reservoir_sample_handles_short_stream():
    sample = reservoir_sample(iter(range(3)), 10, seed=1)
    assert sorted(sample) == [0, 1, 2]


def test_scan_schedule_visits_all_requests():
    order, dist = scan_schedule([5, -3, 8, -1], start=0)
    assert sorted(order) == sorted([5, -3, 8, -1])
    assert dist > 0


def test_scan_policy_commits_direction_until_exhausted():
    policy = ScanPolicy(initial_direction=1)
    pending = {10, 20, -5}
    first = policy.next_target(pending, 0)
    assert first == 10  # nearest-ahead in the up direction, not the globally nearest


def test_anneal_finds_low_cost_on_toy_problem():
    def cost_fn(x):
        return (x - 7) ** 2

    def neighbor_fn(x, rng):
        return x + rng.choice([-1, 1])

    best, best_cost = anneal(0, neighbor_fn, cost_fn, iterations=2000, initial_temp=5.0, cooling=0.995, seed=0)
    assert best_cost <= 4  # within 2 of the optimum at x=7


def test_epidemic_broadcast_reaches_most_nodes():
    def neighbors(n):
        return [(n + 1) % 20, (n - 1) % 20]

    def alive(n, r):
        return True

    informed = epidemic_broadcast(neighbors, origin=0, rounds=25, fanout=2, alive_mask_fn=alive, seed=1)
    assert len(informed) == 20


def test_diffusion_balancing_conserves_total_and_equalizes():
    loads = {0: 100.0, 1: 0.0, 2: 0.0, 3: 0.0}

    def neighbors(n):
        return [(n + 1) % 4, (n - 1) % 4]

    result = diffuse_balance(loads, neighbors, rounds=50, alpha=0.2)
    assert abs(sum(result.values()) - 100.0) < 1e-6
    assert max(result.values()) - min(result.values()) < 5.0


def test_auction_schedule_bounds_wait_via_aging():
    arrivals = [(0, "important", 1)] + [(t, f"flood_{t}", 5) for t in range(100)]
    served = auction_schedule(arrivals, horizon=100, escalation_rate=0.5)
    assert served["important"] is not None
    assert served["important"] < 30


def test_ant_colony_router_reinforces_cheaper_path():
    router = AntColonyRouter(["a", "b"], evaporation=0.2, seed=0)
    for _ in range(50):
        router.update("a", cost=1.0)
        router.update("b", cost=100.0)
    assert router.pheromone["a"] > router.pheromone["b"]


def test_negative_selection_detects_far_patterns():
    assert hamming("0" * 12, "1" * 12) == 12
    assert hamming("0" * 12, "0" * 12) == 0

    det = NegativeSelectionDetector(length=12, alphabet="01", r=4, num_detectors=200, seed=0)
    det.train(["0" * 12])
    assert len(det.detectors) > 0, "negative selection should find detectors against a single training pattern"
    # every surviving detector must, by construction, be far (hamming >= r) from the one
    # training example -- this is the actual negative-selection invariant being relied on.
    assert all(hamming(d, "0" * 12) >= 4 for d in det.detectors)
    # a pattern maximally far from "self" (all 1s) should be flagged anomalous
    assert det.is_anomalous("1" * 12)
    # the training pattern itself must never be flagged (that would be a false positive on self)
    assert not det.is_anomalous("0" * 12)


def test_predator_prey_damping_reduces_amplitude():
    def run(e_damping):
        prey, pred = 15.0, 10.0
        vals = []
        step = make_damped_step(e_damping, a=1.0, b=0.1, c=1.0, d=0.1, dt=0.05)
        for i in range(1000):
            prey, pred = step(prey, pred)
            if i >= 800:
                vals.append(pred)
        return max(vals) - min(vals)

    assert run(0.03) < run(0.0)


def test_ramp_metering_never_admits_above_capacity():
    admission = RampMeteringAdmission(service_rate=10)
    admitted = [admission.tick(40) for _ in range(5)]
    assert all(a <= 10 for a in admitted)


def test_quorum_resolve_picks_majority():
    assert quorum_resolve([("A", 1), ("A", 2), ("B", 9), ("A", 3), ("B", 8)]) == "A"


def test_binary_search_correct_and_logarithmic():
    data = list(range(100_000))
    idx, comparisons = binary_search(data, 54321)
    assert idx == 54321
    assert comparisons <= 20


def test_naive_baselines_behave_as_documented():
    ta = ThresholdAutoscaler(low_mark=8, high_mark=12, step=2)
    assert ta.step(20) == 2
    assert ta.step(1) == -2
    assert ta.step(10) == 0

    data = materialize_then_sample(range(1000), 10, seed=0)
    assert len(data) == 10

    nn = NearestNeighborPolicy()
    assert nn.next_target({5, -5}, 4) == 5

    loads = first_fit_decreasing([5, 5, 5, 5], num_bins=2)
    assert loads == [10.0, 10.0]

    informed = central_fanout_broadcast([0, 1, 2, 3], origin=0, alive_mask_fn=lambda n, r: n != 3)
    assert informed == {0, 1, 2}

    assert static_shortest_path_choice({"a": 5, "b": 2}) == "b"

    zs = ZScoreDetector(threshold=2.0)
    zs.train(["000", "000", "111"])
    assert isinstance(zs.is_anomalous("000"), bool)

    served = strict_priority_schedule([(0, "x", 1), (0, "y", 5)], horizon=2)
    assert served["y"] == 0

    admit_all = AdmitAllPolicy()
    assert admit_all.tick(999) == 999

    assert last_write_wins([("A", 1), ("B", 2)]) == "B"

    assert no_rebalancing({"a": 1}, None, None) == {"a": 1}

    idx, comparisons = linear_scan([1, 2, 3, 4], 3)
    assert idx == 2 and comparisons == 3
