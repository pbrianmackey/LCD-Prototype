"""Heat-diffusion-style load balancing (donor mechanism: physics_heat_diffusion).

Equalizes load via purely local neighbor averaging, repeated over rounds, with
no global coordinator. Symmetric-graph, synchronous update: conserves total
load exactly (a genuine discrete Laplacian smoothing step), so it isn't just
"moving load around and hoping" -- the mechanism actually converges.
"""


def diffuse_balance(loads: dict, neighbors_fn, rounds, alpha=0.15):
    cur = dict(loads)
    for _ in range(rounds):
        new = {}
        for n, v in cur.items():
            neighs = neighbors_fn(n)
            if not neighs:
                new[n] = v
                continue
            flow = sum(cur[m] - v for m in neighs)
            new[n] = v + alpha * flow
        cur = new
    return cur
