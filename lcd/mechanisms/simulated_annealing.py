"""Simulated annealing (donor mechanism: statistical_physics_simulated_annealing).

Escapes local optima via randomized perturbation with a cooling acceptance
schedule, instead of a purely greedy no-backtracking placement rule.
"""
import math
import random


def anneal(initial_state, neighbor_fn, cost_fn, iterations=3000, initial_temp=10.0,
           cooling=0.997, seed=None):
    rng = random.Random(seed)
    current = initial_state
    current_cost = cost_fn(current)
    best, best_cost = current, current_cost
    T = initial_temp
    for _ in range(iterations):
        candidate = neighbor_fn(current, rng)
        candidate_cost = cost_fn(candidate)
        delta = candidate_cost - current_cost
        if delta < 0 or rng.random() < math.exp(-delta / max(T, 1e-9)):
            current, current_cost = candidate, candidate_cost
            if current_cost < best_cost:
                best, best_cost = current, current_cost
        T *= cooling
    return best, best_cost
