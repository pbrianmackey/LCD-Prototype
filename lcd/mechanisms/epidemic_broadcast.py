"""Epidemic / gossip broadcast (donor mechanism: epidemiology_sir_gossip).

Propagates via repeated random local contact instead of a single central
fan-out round, so it degrades gracefully under random per-round node failure.
"""
import random


def epidemic_broadcast(neighbors_fn, origin, rounds, fanout, alive_mask_fn, seed=None):
    rng = random.Random(seed)
    informed = {origin}
    for rnd in range(rounds):
        newly = set()
        for node in list(informed):
            if not alive_mask_fn(node, rnd):
                continue
            neighs = neighbors_fn(node)
            if not neighs:
                continue
            targets = rng.sample(neighs, min(fanout, len(neighs)))
            for t in targets:
                newly.add(t)
        informed |= newly
    return informed
