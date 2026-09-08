"""Predator-prey damping via a carrying-capacity term
(donor mechanism: ecology_predator_prey_damping).

Discretized Lotka-Volterra dynamics. Without a self-limiting term the
predator/prey pair cycles indefinitely (sustained boom-bust oscillation).
Adding a quadratic self-limiting term to the predator equation (a carrying
capacity / logistic damping term) drives the system to a stable equilibrium.
"""


def lv_step(prey, predator, a, b, c, d, e_damping=0.0, dt=0.1):
    dprey = a * prey - b * prey * predator
    dpred = -c * predator + d * prey * predator - e_damping * predator * predator
    new_prey = max(prey + dprey * dt, 0.0)
    new_pred = max(predator + dpred * dt, 0.0)
    return new_prey, new_pred


def make_damped_step(e_damping, a=1.0, b=0.1, c=1.0, d=0.1, dt=0.1):
    """Returns a step function closed over the given damping coefficient."""
    def step(prey, predator):
        return lv_step(prey, predator, a, b, c, d, e_damping=e_damping, dt=dt)
    return step
