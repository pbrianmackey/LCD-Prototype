"""
Shared capability ontology.

This is the fixed, domain-neutral "probe basis" used to project both knowledge-base
cards and benchmark problems into a common capability space. It is authored once,
by hand, before any benchmark problem is written, and is never edited to fit a
specific problem afterwards. That ordering matters: if the glossary were tuned
per-problem it would leak the answer into the representation and the experiment
would be circular.

Each phrase describes a general mechanism-level capability in domain-neutral
language -- no mention of "surgeon", "machinist", "server", "cell", etc. Both
KnowledgeCard capability text and BenchmarkProblem statements get embedded
against this same list (see lcd/vectorspace.py). Cosine similarity to these
45 axes is the "capability vector" C = [c1 ... c45] described in the spec.

This is a deliberately small, hand-authored ontology (v0). Section 3 of the
spec notes that "eventually we don't even want humans deciding the dimensions" --
a natural extension (see README, Limitations) is to learn this basis from data
(e.g. via clustering of card texts) instead of hand-authoring it.
"""

CAPABILITY_GLOSSARY = [
    # --- feedback control ---
    "maintaining a target value despite external disturbances via corrective feedback",
    "proportional correction scaled to the size of the current error",
    "accumulating past error over time to eliminate steady state offset",
    "anticipating future error from the current rate of change",
    "avoiding oscillation by damping a control response",
    "converting a continuous physical process into a discrete control rule",
    "reacting to a threshold crossing with an abrupt on off correction",

    # --- sampling / streaming ---
    "sampling a representative subset from a stream of unknown or unbounded length",
    "processing each item exactly once with bounded memory",
    "preserving uniform probability of inclusion as more items arrive",
    "using statistical variability across many independent trials to average out noise",

    # --- scheduling / geometry ---
    "sweeping in one direction across an ordered space before reversing",
    "minimizing total travel distance by servicing requests in positional order",
    "avoiding backtracking caused by greedily chasing the nearest request",
    "bounding the worst case for an adversarially ordered input",

    # --- optimization ---
    "escaping a local optimum via randomized perturbation",
    "gradually reducing the willingness to accept worse solutions over time",
    "exploring a large combinatorial search space without exhaustive enumeration",
    "trading off exploitation of a known good solution against exploration of new ones",
    "combining and mutating high quality candidate solutions to produce better ones",
    "selecting survivors probabilistically in proportion to fitness",

    # --- epidemic / gossip / redundant propagation ---
    "propagating information through repeated random local contact",
    "achieving robustness to random node or participant failure without central coordination",
    "reaching eventual full coverage through redundant peer to peer relay",
    "distributing decision making so no single point of failure exists",

    # --- diffusion / equalization ---
    "equalizing an unevenly distributed quantity through local neighbor averaging",
    "converging toward balance without any global view of the whole system",
    "modeling diffusion of a quantity across a network as repeated smoothing",

    # --- market / pricing / fairness ---
    "allocating a scarce shared resource by willingness to pay",
    "preventing starvation by letting waiting cost increase over time",
    "bounding worst case wait time for low priority requesters",

    # --- stigmergy / adaptive routing ---
    "reinforcing successful paths while allowing exploration of alternatives",
    "letting a signal evaporate over time so stale information is forgotten",
    "adapting routing or choice probabilistically based on accumulated feedback",
    "coordinating independent agents through indirect environmental traces rather than direct communication",

    # --- anomaly detection ---
    "detecting anomalies by characterizing what is normal rather than what is abnormal",
    "generating negative examples that do not match any known good pattern",
    "flagging anything that matches a detector trained only on absence",

    # --- admission control / congestion ---
    "limiting admission into a system to match downstream service capacity",
    "rejecting excess load early rather than accepting all and degrading later",
    "avoiding congestive collapse where throughput drops under overload",

    # --- consensus / voting ---
    "resolving conflicting values by consulting a majority rather than the most recent",
    "tolerating a minority of stale or delayed participants",
    "requiring agreement from more than half of participants before committing",

    # --- population dynamics ---
    "stabilizing a predator prey style oscillation with a capacity limiting term",
    "introducing a self limiting term so unbounded growth saturates",
    "maintaining a moving population near a stable equilibrium",

    # --- generic / control group (should NOT strongly match most donor mechanisms) ---
    "looking up a value quickly by repeatedly halving a sorted search range",
    "storing and retrieving values by direct indexed position",
]

assert len(CAPABILITY_GLOSSARY) == len(set(CAPABILITY_GLOSSARY)), "duplicate glossary phrase"
