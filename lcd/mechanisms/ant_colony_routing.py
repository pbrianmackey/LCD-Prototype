"""Ant-colony / stigmergic routing (donor mechanism: entomology_ant_colony).

Adapts path choice via evaporating, reinforced pheromone trails rather than a
shortest path computed once and cached forever.
"""
import random


class AntColonyRouter:
    """
    tau_min enforces a pheromone floor (as in Max-Min Ant System): without it,
    a path that goes unused for long enough evaporates to ~0 probability and
    can never be rediscovered even if it later becomes the best option again.
    A floor keeps a standing chance of re-exploration, which is what lets the
    router recover after a regime shift instead of converging prematurely.
    """

    def __init__(self, paths, evaporation=0.15, alpha=1.0, seed=None, tau_min=0.05):
        self.paths = list(paths)
        self.pheromone = {p: 1.0 for p in self.paths}
        self.evaporation = evaporation
        self.alpha = alpha
        self.tau_min = tau_min
        self.rng = random.Random(seed)

    def choose(self):
        weights = [self.pheromone[p] ** self.alpha for p in self.paths]
        total = sum(weights)
        r = self.rng.random() * total
        upto = 0.0
        for p, w in zip(self.paths, weights):
            upto += w
            if upto >= r:
                return p
        return self.paths[-1]

    def update(self, chosen_path, cost):
        for p in self.paths:
            self.pheromone[p] = max(self.tau_min, self.pheromone[p] * (1 - self.evaporation))
        self.pheromone[chosen_path] += 1.0 / max(cost, 1e-6)
