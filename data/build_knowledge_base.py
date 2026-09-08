"""
Authors the persistent knowledge store (data/knowledge_base.jsonl).

Card mix (40 total):
  12 cross-domain DONOR cards  -- the correct mechanism for one benchmark problem,
                                   drawn from a field other than software engineering.
  1  same-domain DONOR card     -- binary search; the *correct* answer to the
                                   "naive_sufficient" control problem, to show LCD
                                   doesn't need to reach outside the field when the
                                   field already has the answer.
  13 same-domain DISTRACTOR cards -- software-engineering techniques that read as
                                   topically on-point (high raw-text similarity to
                                   their target problem) but fail the discriminating
                                   test. These exist so the RAG baseline has a
                                   genuine, fair, plausible-looking option to retrieve.
  14 NOISE cards                -- unrelated domains, solve none of the benchmark
                                   problems. Included so retrieval has to find a
                                   needle in a realistically sized haystack rather
                                   than pick from a curated shortlist.

Every donor card's `text` field is written the way a domain reference/encyclopedia
would write it -- no software-engineering vocabulary, no mention of the target
benchmark problem. `mechanism_template` is the abstracted, domain-neutral version
(this is what lcd/pipeline.py's Abstractor is standing in for -- see README).
`capability_tags` are short, independently-worded, domain-neutral phrases.

IMPORTANT: nothing here encodes "problem X's required capabilities = card Y's
tags" as a lookup table. The only link between a problem and its true donor card
is BenchmarkProblem.donor_card_id, which is used solely for after-the-fact scoring
(cross-representation distance, LDR-by-condition) -- it is never given to either
retriever. Retrieval only ever sees problem.statement and card text fields.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lcd.schema import KnowledgeCard, save_cards

CARDS = []


def add(**kw):
    CARDS.append(KnowledgeCard(**kw))


# ============================== DONOR CARDS (cross-domain) ==============================

add(
    id="control_theory_pid",
    domain="control_theory",
    title="PID Feedback Control",
    text=(
        "A proportional-integral-derivative (PID) controller continuously computes an error "
        "value e(t) as the difference between a desired setpoint and a measured process "
        "variable, then applies a correction u(t) = Kp*e(t) + Ki*integral(e) + Kd*(de/dt). "
        "The proportional term reacts to the present error, the integral term eliminates "
        "residual steady-state offset by accumulating past error, and the derivative term "
        "damps the response by anticipating where the error is heading. Poorly tuned gains, "
        "or a controller with only an on/off proportional term, tend to overshoot and "
        "oscillate around the setpoint, especially when the plant has lag between an action "
        "and its measured effect. PID loops are used in thermostats, cruise control, "
        "servo motors and industrial process control."
    ),
    capability_tags=[
        "maintain a target value under disturbance via corrective feedback",
        "proportional correction scaled to current error",
        "integral term removes steady state offset",
        "derivative term anticipates and damps oscillation",
        "handles delayed effect between action and measured result",
    ],
    mechanism_template=(
        "Given a measured quantity, a target setpoint, and an actuator whose effect on the "
        "quantity is delayed, maintain the target value despite disturbances via corrective "
        "feedback: compute error = target - measured; correction = Kp*error + "
        "Ki*sum(error over time) + Kd*(change in error); apply correction each tick. This "
        "damps oscillation that a simple threshold on/off rule produces when there is lag "
        "between action and effect."
    ),
    domain_terms=["PID", "setpoint", "plant", "proportional", "integral", "derivative", "servo", "actuator"],
    code_skeleton="lcd.mechanisms.pid.PIDController",
    is_distractor=False,
)

add(
    id="statistics_reservoir_sampling",
    domain="statistics",
    title="Reservoir Sampling",
    text=(
        "Reservoir sampling (Algorithm R, Vitter 1985) draws a uniform random sample of size "
        "k from a population of unknown or unbounded size, seen only once, in order, with no "
        "ability to know the total count in advance and no ability to revisit earlier items. "
        "The first k items fill the reservoir. Each subsequent item i (0-indexed, i >= k) "
        "replaces a uniformly random slot in the reservoir with probability k/(i+1); "
        "otherwise it is discarded. This preserves an exactly uniform probability of "
        "inclusion for every item that has been seen so far, at every point in the pass, "
        "using O(k) memory regardless of how long the stream turns out to be."
    ),
    capability_tags=[
        "sample a representative subset from a stream of unknown length",
        "single pass, bounded memory per item",
        "preserve uniform inclusion probability as more items arrive",
        "no need to know total count in advance",
    ],
    mechanism_template=(
        "Given a sequence that can only be read once, in order, of unknown total length, "
        "produce a uniformly random subset of size k using O(k) memory: keep the first k "
        "items; for the i-th subsequent item, replace a uniformly chosen slot with "
        "probability k/(i+1), else discard the item. Never materialize the full sequence."
    ),
    domain_terms=["reservoir", "Algorithm R", "unbiased estimator", "sampling without replacement"],
    code_skeleton="lcd.mechanisms.reservoir_sampling.reservoir_sample",
    is_distractor=False,
)

add(
    id="logistics_elevator_scan",
    domain="operations_research",
    title="SCAN / Elevator Servicing",
    text=(
        "The elevator algorithm (SCAN) services pending stop requests along a single "
        "physical track by continuing to sweep in its current direction, picking up every "
        "request that lies in its path, until it reaches the end of the track, then reversing "
        "direction. This is the standard model for how elevators and, by direct analogy, "
        "hard-disk arms service requests scattered along a line: a car heading up serves "
        "every call above it before ever heading down, rather than peeling off toward "
        "whichever call happens to be nearest at each instant, which can cause the car to "
        "reverse direction repeatedly and re-traverse the same stretch of track over and "
        "over on an unfavorable request pattern."
    ),
    capability_tags=[
        "sweep in one direction across an ordered space before reversing",
        "minimize total travel by servicing requests in positional order",
        "avoid backtracking from chasing the nearest request",
        "bounded worst case travel distance on an adversarial request order",
    ],
    mechanism_template=(
        "Given pending requests at positions along a 1-D line and an agent that starts at "
        "some position, minimize total travel distance: sweep monotonically in the current "
        "direction, servicing every pending request encountered along the way, then reverse "
        "at the end of the line and sweep back. This bounds the worst-case backtracking that "
        "a pure nearest-request-first rule suffers when requests keep appearing on "
        "alternating sides."
    ),
    domain_terms=["SCAN", "elevator algorithm", "disk arm", "seek", "track"],
    code_skeleton="lcd.mechanisms.scan_scheduling.scan_schedule",
    is_distractor=False,
)

add(
    id="statistical_physics_simulated_annealing",
    domain="statistical_physics",
    title="Simulated Annealing",
    text=(
        "In metallurgical annealing, a material is heated and then cooled slowly so that its "
        "atoms have time to settle into a low-energy, highly ordered crystal lattice instead "
        "of freezing into a disordered, higher-energy state. Simulated annealing borrows this "
        "cooling schedule as a search strategy: a candidate configuration is perturbed at "
        "random, and the perturbed configuration is accepted if it improves the objective, or "
        "accepted anyway with a probability that depends on how much worse it is and on a "
        "temperature parameter that starts high and is lowered over the course of the run. "
        "Early on, high temperature lets the search accept worse configurations and jump out "
        "of a locally best arrangement it has wandered into; as the temperature falls the "
        "search increasingly only accepts improvements, settling into a good configuration "
        "rather than the first mediocre one it stumbled on."
    ),
    capability_tags=[
        "escape a local optimum via randomized perturbation",
        "gradually reduce willingness to accept worse candidates over time",
        "explore a large combinatorial arrangement space without exhaustive search",
        "temperature schedule trades exploration for exploitation",
    ],
    mechanism_template=(
        "Given a combinatorial assignment problem where a greedy or first-fit rule can get "
        "stuck in a locally-best-but-globally-poor arrangement, search by randomly perturbing "
        "the current arrangement and accepting the perturbation if it is better, or with "
        "probability exp(-delta/T) if it is worse; lower T over successive iterations "
        "according to a cooling schedule. This lets the search escape local optima that a "
        "purely greedy, no-backtracking assignment rule cannot."
    ),
    domain_terms=["annealing", "lattice", "temperature schedule", "Metropolis criterion", "quenching"],
    code_skeleton="lcd.mechanisms.simulated_annealing.anneal",
    is_distractor=False,
)

add(
    id="epidemiology_sir_gossip",
    domain="epidemiology",
    title="Epidemic Spread and Herd Coverage",
    text=(
        "In compartmental epidemic models (SIR), an infection spreads through a population by "
        "repeated contact between infectious and susceptible individuals; each infectious "
        "individual has some chance, each time step, of passing the infection to each "
        "susceptible contact. Even without any central authority directing the spread, and "
        "even though any single contact might fail to transmit or a given individual might "
        "be briefly unreachable, repeated random local contact over enough rounds reaches "
        "near-total coverage of a well-mixed population, because the individuals who did not "
        "transmit or receive in one round get further chances in later rounds. Coverage "
        "degrades gracefully as the per-contact transmission probability or the per-round "
        "reachability of individuals falls, rather than failing outright."
    ),
    capability_tags=[
        "propagate information through repeated random local contact",
        "robust to random participant failure without central coordination",
        "reach eventual near-total coverage through redundant relay over many rounds",
        "degrades gracefully rather than failing outright when some contacts fail",
    ],
    mechanism_template=(
        "Given a population of nodes and one origin holding an update, where any node can be "
        "transiently unreachable in a given round and there is no reliable central "
        "broadcaster, propagate the update to (nearly) everyone by having every node that "
        "already holds the update forward it to a small number of random peers each round, "
        "repeated over multiple rounds. Reachability failures in one round are compensated "
        "for by further chances in subsequent rounds, so coverage approaches 100% "
        "probabilistically rather than requiring any single round to succeed."
    ),
    domain_terms=["SIR model", "susceptible", "infectious", "herd immunity", "compartmental model", "R0"],
    code_skeleton="lcd.mechanisms.epidemic_broadcast.epidemic_broadcast",
    is_distractor=False,
)

add(
    id="physics_heat_diffusion",
    domain="physics",
    title="Heat Diffusion and Discrete Laplacian Smoothing",
    text=(
        "Heat diffuses through a solid according to Fourier's law: the flow of heat between "
        "two adjacent points is proportional to the temperature difference between them, so "
        "hot spots cool and cold spots warm until the temperature field is even. Discretized "
        "on a graph or grid, this becomes a purely local update rule: each point's next "
        "temperature is a weighted average of its own current temperature and its immediate "
        "neighbors' temperatures. No point ever needs to know the global temperature "
        "distribution; repeating the local averaging rule enough times drives the whole "
        "system toward a uniform equilibrium, with the rate of convergence governed by how "
        "well connected the graph is."
    ),
    capability_tags=[
        "equalize an unevenly distributed quantity through local neighbor averaging",
        "converge toward global balance with no global view",
        "purely local update rule applied repeatedly across a network",
    ],
    mechanism_template=(
        "Given a quantity distributed unevenly across nodes of a network, where each node "
        "can only see its direct neighbors, equalize the distribution by repeatedly setting "
        "each node's value to a weighted average of its own value and its neighbors' values. "
        "No global coordinator or global view is required; repeated local averaging alone "
        "drives the system toward equilibrium."
    ),
    domain_terms=["Fourier's law", "thermal equilibrium", "Laplacian", "diffusion coefficient", "discretization"],
    code_skeleton="lcd.mechanisms.diffusion_balancing.diffuse_balance",
    is_distractor=False,
)

add(
    id="economics_congestion_pricing_aging",
    domain="economics",
    title="Congestion Pricing and Willingness-to-Pay Allocation",
    text=(
        "Markets allocate a scarce resource by letting participants signal how much they "
        "value access, rather than serving strictly in the order requests arrived or by a "
        "fixed rank. A common refinement used in congestion pricing and auction design is to "
        "let a participant's effective bid rise the longer they have been waiting, so that "
        "even a participant with modest base value is eventually served rather than being "
        "perpetually outbid by a steady stream of new, nominally higher-value arrivals. This "
        "bounds worst-case waiting time for every participant while still favoring higher "
        "value requests when wait times are otherwise equal."
    ),
    capability_tags=[
        "allocate a scarce shared resource by willingness to pay",
        "let waiting cost increase over time to prevent starvation",
        "bound worst case wait time for lower priority requesters",
    ],
    mechanism_template=(
        "Given many requesters competing for one shared resource, each with a base value and "
        "an arrival time, where serving strictly by fixed value or fixed class can starve "
        "some requesters indefinitely, allocate the resource each round to the requester with "
        "the highest effective bid, where effective bid = base value + (waiting time) * "
        "(escalation rate). This guarantees every requester's effective bid eventually "
        "dominates, bounding worst-case wait time, while still respecting relative value."
    ),
    domain_terms=["willingness to pay", "Vickrey auction", "congestion pricing", "bid escalation", "market clearing"],
    code_skeleton="lcd.mechanisms.auction_scheduling.auction_schedule",
    is_distractor=False,
)

add(
    id="entomology_ant_colony",
    domain="entomology",
    title="Ant Foraging and Stigmergic Trails",
    text=(
        "Foraging ants lay down a chemical pheromone trail as they return from a food source, "
        "and other ants are more likely to follow paths with a stronger trail. Pheromone "
        "evaporates over time, so trails on paths that are no longer being reinforced fade, "
        "while trails on paths that continue to be used (because they are short, or because "
        "the food source is still there) stay strong. No ant has a map of the whole terrain "
        "or communicates a plan directly to any other ant; the colony's routing adapts purely "
        "through this shared, indirect, decaying trace left in the environment, so it "
        "re-routes automatically if a previously good path becomes blocked or a shorter one "
        "becomes available."
    ),
    capability_tags=[
        "reinforce successful paths while allowing exploration of alternatives",
        "let a signal evaporate over time so stale information is forgotten",
        "adapt routing probabilistically from accumulated indirect feedback",
        "coordinate independent agents without direct communication",
    ],
    mechanism_template=(
        "Given a network whose edge costs change over time and must be routed over "
        "repeatedly, adapt routing without recomputing a full global shortest path each time: "
        "maintain a trail strength per edge; each trip, choose a path probabilistically "
        "favoring higher-trail edges, then reinforce the edges used in proportion to how good "
        "the trip was; evaporate all trail strengths slightly every round. This lets routing "
        "drift toward newly-cheap edges and away from newly-congested ones using only local, "
        "indirect feedback."
    ),
    domain_terms=["pheromone", "stigmergy", "foraging", "trail evaporation", "colony"],
    code_skeleton="lcd.mechanisms.ant_colony_routing.AntColonyRouter",
    is_distractor=False,
)

add(
    id="immunology_negative_selection",
    domain="immunology",
    title="Immune Negative Selection",
    text=(
        "The adaptive immune system generates a large, diverse population of T-cells with "
        "randomly generated receptors, then discards (negatively selects) any T-cell whose "
        "receptor binds strongly to the body's own healthy tissue. The T-cells that survive "
        "this screening are, by construction, ones that do not react to self; because they "
        "were never trained against examples of actual pathogens, this process can flag "
        "previously unseen invaders as foreign simply by virtue of not looking like self, "
        "without ever needing a labeled catalogue of what pathogens look like."
    ),
    capability_tags=[
        "detect anomalies by characterizing what is normal rather than what is abnormal",
        "generate negative detectors that do not match any known good pattern",
        "flag anything that matches a detector trained only on the absence of abnormal examples",
        "requires no labeled examples of the anomaly itself",
    ],
    mechanism_template=(
        "Given only examples of 'normal' patterns and no labeled examples of anomalies, "
        "detect novel anomalies as follows: generate a large population of random candidate "
        "detectors; discard any detector that matches (is too similar to) any normal training "
        "example; keep the surviving detectors. At test time, flag any new pattern that "
        "matches one or more surviving detectors as anomalous. This requires no labeled "
        "anomaly data and can catch structurally unusual patterns that a simple numeric "
        "threshold on summary statistics would miss."
    ),
    domain_terms=["T-cell", "negative selection", "self/non-self discrimination", "receptor", "antigen"],
    code_skeleton="lcd.mechanisms.negative_selection.NegativeSelectionDetector",
    is_distractor=False,
)

add(
    id="ecology_predator_prey_damping",
    domain="ecology",
    title="Predator-Prey Dynamics and Carrying Capacity",
    text=(
        "The Lotka-Volterra equations show that a predator population that simply grows "
        "whenever prey are abundant and shrinks whenever prey are scarce, with no other "
        "limit, produces sustained boom-bust oscillation: predators overshoot as prey are "
        "plentiful, crash the prey population, then starve and crash themselves, repeating "
        "indefinitely. Adding a carrying-capacity term -- a self-limiting factor that caps "
        "growth as a population approaches the resource ceiling the environment can support, "
        "independent of the other population's momentary abundance -- damps this oscillation "
        "and lets both populations settle toward a stable equilibrium instead of cycling."
    ),
    capability_tags=[
        "stabilize a boom bust oscillation with a capacity limiting term",
        "introduce a self limiting term so unbounded reactive growth saturates",
        "settle toward stable equilibrium instead of cycling",
    ],
    mechanism_template=(
        "Given two coupled quantities that each grow or shrink purely in reaction to the "
        "other's current level (producing sustained oscillation), stabilize the system by "
        "adding a self-limiting term to each population's growth rule that caps its growth "
        "rate as it approaches a fixed capacity ceiling, independent of the other quantity's "
        "momentary level. This damps the reactive boom-bust cycle into a stable equilibrium."
    ),
    domain_terms=["Lotka-Volterra", "carrying capacity", "predator-prey", "population dynamics", "logistic growth"],
    code_skeleton="lcd.mechanisms.predator_prey_damping.damped_scaling_step",
    is_distractor=False,
)

add(
    id="transportation_ramp_metering",
    domain="transportation_engineering",
    title="Highway Ramp Metering",
    text=(
        "Freeway traffic flow exhibits a capacity drop: once density past a merge point "
        "exceeds a critical threshold, throughput actually falls, because vehicles are forced "
        "to brake and merge in stop-and-go conditions that waste capacity relative to smooth "
        "free-flow merging. Ramp metering controls the rate at which vehicles are admitted "
        "onto the freeway from an on-ramp, holding admitted flow below the point that would "
        "trigger the breakdown, queuing excess vehicles at the ramp rather than on the "
        "freeway itself. Counterintuitively, admitting traffic more slowly at the on-ramp "
        "increases total throughput measured downstream, compared with admitting every "
        "vehicle immediately and letting the freeway itself absorb the overload."
    ),
    capability_tags=[
        "limit admission into a system to match downstream capacity",
        "reject or queue excess load at the edge rather than accepting all of it",
        "avoid a capacity collapse where throughput drops under overload",
    ],
    mechanism_template=(
        "Given a shared downstream resource with a known service rate, where accepting every "
        "incoming request immediately causes throughput to collapse under overload (a "
        "capacity drop from thrashing/contention), admit requests at a rate that matches "
        "downstream capacity and hold or reject the rest at the point of entry, rather than "
        "admitting everything and letting congestion form inside the system. This keeps "
        "achieved throughput near capacity even as offered load grows far past it."
    ),
    domain_terms=["ramp metering", "capacity drop", "freeway", "merge", "stop-and-go"],
    code_skeleton="lcd.mechanisms.ramp_metering.RampMeteringAdmission",
    is_distractor=False,
)

add(
    id="social_choice_quorum_voting",
    domain="social_choice_theory",
    title="Majority Quorum Voting",
    text=(
        "Voting theory distinguishes deciding an outcome by whichever proposal was submitted "
        "most recently from deciding by which proposal the largest bloc of voters actually "
        "holds. Consulting only the most recent submission is vulnerable to a small, "
        "possibly unrepresentative subset of voters having the last word purely due to "
        "timing. Requiring agreement from a quorum -- more than half of eligible voters -- "
        "before an outcome is accepted instead selects whichever value the majority actually "
        "holds, and is robust to a minority of participants being slow, offline, or reporting "
        "stale information, since their votes simply do not change which value has a majority."
    ),
    capability_tags=[
        "resolve conflicting values by consulting a majority rather than the most recent",
        "require agreement from more than half of participants before committing",
        "tolerate a minority of stale or delayed participants",
    ],
    mechanism_template=(
        "Given several participants reporting possibly conflicting values, where deciding "
        "by whichever value arrived last is vulnerable to network delay putting a stale or "
        "minority value last, decide instead by collecting reports from a quorum (more than "
        "half) of participants and selecting the value held by the majority of that quorum. "
        "This is robust to a minority of participants being delayed or holding stale values."
    ),
    domain_terms=["quorum", "Condorcet", "plurality", "electorate", "bloc voting"],
    code_skeleton="lcd.mechanisms.quorum_consensus.quorum_resolve",
    is_distractor=False,
)

# ---- same-domain donor (control: naive-sufficient) ----
add(
    id="cs_binary_search",
    domain="computer_science",
    title="Binary Search",
    text=(
        "Binary search finds a target value in a sorted array by repeatedly comparing the "
        "target to the middle element of the current range and discarding the half of the "
        "range that cannot contain the target, halving the remaining range each comparison. "
        "This finds or rules out any target in a sorted array of n elements in O(log n) "
        "comparisons, far fewer than scanning every element in order."
    ),
    capability_tags=[
        "look up a value quickly by repeatedly halving a sorted search range",
        "logarithmic worst case comparisons on sorted data",
    ],
    mechanism_template=(
        "Given a sorted, randomly-indexable collection and a target value, find it (or "
        "determine its absence) in O(log n) comparisons by repeatedly comparing against the "
        "midpoint of the current range and discarding the half that cannot contain the "
        "target."
    ),
    domain_terms=["binary search", "sorted array", "midpoint", "log n"],
    code_skeleton="lcd.mechanisms.binary_search.binary_search",
    is_distractor=False,
)


# ============================== DISTRACTOR CARDS (same-domain, plausible, insufficient) ==============================

add(
    id="se_threshold_autoscaling",
    domain="software_engineering",
    title="Threshold-Based Autoscaling",
    text=(
        "A common autoscaling approach adds a worker whenever the request queue length rises "
        "above a high-water mark and removes a worker whenever it falls below a low-water "
        "mark. This is simple to implement and reason about and is the default in many "
        "container orchestration and autoscaling products."
    ),
    capability_tags=["reacts to threshold crossing with an abrupt on/off adjustment", "simple to implement"],
    mechanism_template=(
        "Adjust capacity by a fixed step whenever a monitored quantity crosses a fixed "
        "high/low threshold."
    ),
    domain_terms=["autoscaling", "high-water mark", "worker pool", "container orchestration"],
    code_skeleton="lcd.mechanisms.naive_baselines.threshold_autoscale",
    is_distractor=True,
)

add(
    id="se_materialize_then_sample",
    domain="software_engineering",
    title="Collect-Then-Sample",
    text=(
        "A straightforward way to draw a random sample from a data source is to load every "
        "record into a list and then call a standard library random-sampling function on "
        "the full list. This pattern appears throughout data pipelines and is simple, "
        "correct, and easy to test for any input that comfortably fits in memory."
    ),
    capability_tags=["load all data then sample", "simple and easy to test", "requires knowing input fits in memory"],
    mechanism_template="Materialize the entire input into memory, then sample uniformly from the materialized collection.",
    domain_terms=["ETL pipeline", "in-memory list", "random.sample"],
    code_skeleton="lcd.mechanisms.naive_baselines.materialize_then_sample",
    is_distractor=True,
)

add(
    id="se_nearest_neighbor_dispatch",
    domain="software_engineering",
    title="Nearest-Request-First Dispatch",
    text=(
        "A simple dispatch rule for a mobile picker or courier is to always send it to "
        "whichever pending request is currently closest. This greedily minimizes the very "
        "next hop and is easy to implement with a distance comparison over the pending "
        "request list."
    ),
    capability_tags=["greedily serve the closest pending request", "simple, local, easy to reason about"],
    mechanism_template="Always move to whichever pending request minimizes immediate distance from the current position.",
    domain_terms=["dispatch", "courier routing", "greedy nearest neighbor"],
    code_skeleton="lcd.mechanisms.naive_baselines.nearest_neighbor_dispatch",
    is_distractor=True,
)

add(
    id="se_first_fit_decreasing",
    domain="software_engineering",
    title="First-Fit-Decreasing Bin Packing",
    text=(
        "A standard heuristic for assigning variously-sized jobs to a fixed set of machines "
        "is first-fit-decreasing: sort jobs from largest to smallest, then place each job on "
        "the first machine with enough remaining capacity (or, for load balancing, the "
        "currently least-loaded machine). It is widely used because it is fast, simple, and "
        "usually close to optimal."
    ),
    capability_tags=["sort by size then greedily place", "usually close to optimal", "no backtracking"],
    mechanism_template="Sort items by decreasing size; place each item greedily into the currently-best-fitting bin; never reconsider a placement.",
    domain_terms=["bin packing", "first-fit-decreasing", "makespan", "load balancer"],
    code_skeleton="lcd.mechanisms.naive_baselines.first_fit_decreasing",
    is_distractor=True,
)

add(
    id="se_central_fanout_broadcast",
    domain="software_engineering",
    title="Central Fan-Out Broadcast",
    text=(
        "The simplest way to replicate an update to many nodes is for the node that received "
        "the write to open a connection to every other node and push the update directly. "
        "This minimizes latency to each recipient when it works and is the default design in "
        "many single-writer replication systems."
    ),
    capability_tags=["one node pushes directly to every other node", "low latency in the common case", "single round"],
    mechanism_template="The origin node sends the update directly to every other node in one round; there is no retry or relay by recipients.",
    domain_terms=["fan-out", "single-writer replication", "push replication"],
    code_skeleton="lcd.mechanisms.naive_baselines.central_fanout_broadcast",
    is_distractor=True,
)

add(
    id="se_static_shortest_path",
    domain="software_engineering",
    title="Precomputed Static Shortest-Path Table",
    text=(
        "Many routing layers compute shortest paths once, offline, from a snapshot of link "
        "costs, and cache the resulting routing table for fast lookup at request time. This "
        "avoids the cost of recomputing shortest paths on every request and is standard "
        "practice when link costs are expected to be fairly stable."
    ),
    capability_tags=["precompute once, cache, and reuse", "fast lookup", "assumes costs are stable"],
    mechanism_template="Compute the globally optimal routing table once from a fixed snapshot of costs, then reuse it for all future requests without updating it.",
    domain_terms=["routing table", "offline precomputation", "cache", "link cost snapshot"],
    code_skeleton="lcd.mechanisms.naive_baselines.static_shortest_path_router",
    is_distractor=True,
)

add(
    id="se_zscore_outlier",
    domain="software_engineering",
    title="Z-Score Outlier Detection",
    text=(
        "A common approach to flagging anomalous log lines or metric readings is to compute "
        "a numeric summary statistic (such as request rate or response size), fit a mean and "
        "standard deviation from historical normal traffic, and flag any new reading whose "
        "z-score exceeds a fixed number of standard deviations. It is cheap to compute and "
        "widely used in monitoring dashboards."
    ),
    capability_tags=["flag values far from the historical mean", "cheap, single numeric threshold", "assumes a roughly normal distribution"],
    mechanism_template="Fit mean and standard deviation of a single summary statistic from normal examples; flag new values whose z-score exceeds a fixed threshold.",
    domain_terms=["z-score", "standard deviation", "monitoring dashboard", "alert threshold"],
    code_skeleton="lcd.mechanisms.naive_baselines.zscore_detector",
    is_distractor=True,
)

add(
    id="se_strict_priority_queue",
    domain="software_engineering",
    title="Strict Priority Queue Scheduling",
    text=(
        "A simple way to make sure important work gets done first is a strict priority "
        "queue: always run the highest-priority ready task, and only run a lower-priority "
        "task when no higher-priority task is ready. This is simple to implement with a heap "
        "and is a common default in task schedulers."
    ),
    capability_tags=["always run the highest fixed priority task", "simple, heap-based", "no aging"],
    mechanism_template="Maintain tasks in strict priority order; always dispatch the highest-priority ready task; priority never changes while a task waits.",
    domain_terms=["priority queue", "heap", "task scheduler", "priority inversion"],
    code_skeleton="lcd.mechanisms.naive_baselines.strict_priority_schedule",
    is_distractor=True,
)

add(
    id="se_admit_all_retry",
    domain="software_engineering",
    title="Admit-All With Client Retry",
    text=(
        "A common design accepts every incoming request immediately and relies on "
        "timeouts and client-side retry to smooth out any overload, rather than rejecting or "
        "queuing requests at the front door. This keeps the server simple and gives clients "
        "the best possible latency whenever the system is not overloaded."
    ),
    capability_tags=["accept everything immediately", "push overload handling to timeouts and retries", "simple server logic"],
    mechanism_template="Accept every request on arrival regardless of current load; rely on downstream timeouts and client retries to eventually get through.",
    domain_terms=["admission", "client retry", "timeout", "backend queue"],
    code_skeleton="lcd.mechanisms.naive_baselines.admit_all_with_retry",
    is_distractor=True,
)

add(
    id="se_last_write_wins",
    domain="software_engineering",
    title="Last-Write-Wins Conflict Resolution",
    text=(
        "When two replicas report different values for the same key, a simple and popular "
        "resolution rule is last-write-wins: keep whichever value carries the most recent "
        "timestamp and discard the rest. It requires no coordination between replicas and is "
        "the default conflict-resolution strategy in a number of widely used data stores."
    ),
    capability_tags=["keep the most recent timestamp", "no coordination required", "simple, single comparison"],
    mechanism_template="Among conflicting reported values, keep whichever carries the latest timestamp and discard the others; never consult how many replicas hold each value.",
    domain_terms=["last-write-wins", "timestamp", "replica", "eventual consistency"],
    code_skeleton="lcd.mechanisms.naive_baselines.last_write_wins",
    is_distractor=True,
)

add(
    id="se_reactive_worker_step",
    domain="software_engineering",
    title="Reactive One-Step Worker Adjustment",
    text=(
        "A lightweight way to keep a worker pool matched to load is to add exactly one "
        "worker whenever the backlog grew since the last check, and remove exactly one "
        "worker whenever it shrank. It requires no tuning of gains or thresholds beyond the "
        "step size and check interval."
    ),
    capability_tags=["react to the sign of recent backlog change", "adjust by a fixed step", "no capacity limit term"],
    mechanism_template="Each tick, add one unit of capacity if the monitored backlog grew since last tick, remove one unit if it shrank; the adjustment rule has no term limiting growth as capacity nears a ceiling.",
    domain_terms=["worker pool", "backlog", "step adjustment"],
    code_skeleton="lcd.mechanisms.naive_baselines.reactive_worker_step",
    is_distractor=True,
)

add(
    id="se_no_rebalancing",
    domain="software_engineering",
    title="Static Assignment, No Rebalancing",
    text=(
        "The simplest way to spread load across a fixed set of servers is to assign each "
        "unit of work to a server once, at creation time (for example by a hash of its key), "
        "and never move it afterward. This avoids the operational complexity of migrating "
        "live work between servers."
    ),
    capability_tags=["assign once at creation, never move", "no ongoing coordination needed", "avoids migration complexity"],
    mechanism_template="Assign each unit of load to a server once via a fixed rule (e.g. a hash); never re-examine or rebalance the assignment afterward, regardless of how uneven load becomes.",
    domain_terms=["consistent hashing", "static sharding", "no rebalancing"],
    code_skeleton="lcd.mechanisms.naive_baselines.no_rebalancing",
    is_distractor=True,
)

add(
    id="se_linear_scan",
    domain="software_engineering",
    title="Linear Scan Lookup",
    text=(
        "The most straightforward way to check whether a value is present in a list is to "
        "walk the list from the beginning and compare each element until a match is found or "
        "the list is exhausted. It requires no preprocessing or ordering assumption on the "
        "data."
    ),
    capability_tags=["scan every element in order", "no ordering assumption required", "simple to implement"],
    mechanism_template="Check membership by comparing the target against every element in sequence until found or exhausted; O(n) comparisons worst case.",
    domain_terms=["linear scan", "membership check", "unsorted list"],
    code_skeleton="lcd.mechanisms.naive_baselines.linear_scan",
    is_distractor=True,
)


# ============================== NOISE CARDS (unrelated domains) ==============================

NOISE = [
    dict(id="art_rule_of_thirds", domain="visual_art", title="Rule of Thirds Composition",
         text="Placing key subjects along lines that divide an image into thirds, rather than dead center, tends to produce a more dynamic, balanced composition in painting and photography.",
         capability_tags=["balance visual weight off-center", "guide the eye along compositional lines"],
         mechanism_template="Distribute visual emphasis away from the exact center to create dynamic balance.",
         domain_terms=["composition", "focal point", "visual balance"]),
    dict(id="culinary_maillard_reaction", domain="culinary_science", title="The Maillard Reaction",
         text="Browning and flavor development in seared meat and toasted bread result from the Maillard reaction, a chemical reaction between amino acids and reducing sugars that requires high heat and a relatively dry surface.",
         capability_tags=["chemical browning under high heat", "requires a dry surface to proceed"],
         mechanism_template="A surface reaction between two reactive components proceeds only above a heat and dryness threshold, producing new flavor compounds.",
         domain_terms=["Maillard reaction", "searing", "amino acids"]),
    dict(id="music_counterpoint", domain="music_theory", title="Counterpoint Voice Leading",
         text="In species counterpoint, independent melodic voices are combined so each remains singable and consonant with the others at every beat, with rules governing how voices may move relative to one another.",
         capability_tags=["combine independent lines while preserving local consonance", "constrain relative motion between voices"],
         mechanism_template="Combine multiple independent sequences under local pairwise constraints so the combination remains well-formed at every step.",
         domain_terms=["counterpoint", "consonance", "voice leading"]),
    dict(id="linguistics_zipfs_law", domain="linguistics", title="Zipf's Law",
         text="Across natural languages, the frequency of a word is roughly inversely proportional to its rank in a frequency table: a small number of words account for most word occurrences, with a long tail of rare words.",
         capability_tags=["a small set of items accounts for most occurrences", "long tail distribution"],
         mechanism_template="Item frequency follows a heavy-tailed rank distribution where a small head accounts for most of the mass.",
         domain_terms=["Zipf's law", "rank-frequency", "corpus linguistics"]),
    dict(id="astronomy_orbital_resonance", domain="astronomy", title="Orbital Resonance",
         text="Two orbiting bodies are in orbital resonance when their orbital periods form a ratio of small integers, such as 2:1; the repeated gravitational tugs at the same relative points in each orbit can stabilize or destabilize the orbits over long timescales.",
         capability_tags=["repeated periodic interaction at matching phase", "can stabilize or destabilize over long timescales"],
         mechanism_template="Two periodic processes whose periods are in a small integer ratio interact repeatedly at the same relative phase, reinforcing an effect over many cycles.",
         domain_terms=["orbital resonance", "orbital period", "gravitational perturbation"]),
    dict(id="architecture_flying_buttress", domain="architecture", title="The Flying Buttress",
         text="Gothic cathedrals use flying buttresses, external arched supports, to carry the lateral thrust of a stone vault away from the walls and down to the ground, allowing the walls themselves to be thinner and to hold larger windows.",
         capability_tags=["redirect lateral load away from a thin wall to an external support", "allows the primary structure to be lighter"],
         mechanism_template="Redirect a lateral structural load through an external support path so the primary enclosing structure can be lighter.",
         domain_terms=["flying buttress", "lateral thrust", "vault"]),
    dict(id="geology_plate_tectonics", domain="geology", title="Subduction Zones",
         text="Where one tectonic plate is denser than the plate it meets, it slides beneath the other into the mantle at a subduction zone, a process associated with deep ocean trenches, volcanic arcs, and the majority of the world's largest earthquakes.",
         capability_tags=["denser layer slides beneath a less dense one", "releases energy at the boundary"],
         mechanism_template="Where two bulk masses of different density meet, the denser one slides beneath the other, releasing accumulated stress at the boundary.",
         domain_terms=["subduction", "tectonic plate", "volcanic arc"]),
    dict(id="sports_zone_defense", domain="sports", title="Zone Defense",
         text="In zone defense, each defender is responsible for a fixed area of the court or field rather than a specific opposing player, handing off responsibility for an attacker as they move between zones.",
         capability_tags=["cover a fixed region rather than a specific target", "hand off responsibility at a boundary"],
         mechanism_template="Assign responsibility by region rather than by specific target, handing off as the target crosses a region boundary.",
         domain_terms=["zone defense", "man-to-man", "handoff"]),
    dict(id="chemistry_catalysis", domain="chemistry", title="Catalysis",
         text="A catalyst speeds up a chemical reaction by providing an alternative reaction pathway with lower activation energy, without itself being consumed by the reaction, so a small amount of catalyst can process a very large amount of reactant over time.",
         capability_tags=["lower the energy barrier of a process without being consumed", "small amount enables large throughput"],
         mechanism_template="Provide an alternative low-barrier pathway for a process, without being consumed, so a small facilitating resource enables much larger throughput.",
         domain_terms=["catalyst", "activation energy", "reaction pathway"]),
    dict(id="meteorology_pressure_gradient", domain="meteorology", title="Pressure Gradient Wind",
         text="Wind arises from air moving from areas of high atmospheric pressure to areas of low pressure, with the strength of the wind proportional to how steep the pressure gradient is between the two areas.",
         capability_tags=["flow from high to low potential", "flow rate proportional to gradient steepness"],
         mechanism_template="A quantity flows from a region of higher potential to lower potential at a rate proportional to the steepness of the gradient between them.",
         domain_terms=["pressure gradient", "isobar", "atmospheric pressure"]),
    dict(id="law_stare_decisis", domain="law", title="Stare Decisis",
         text="Under the doctrine of stare decisis, courts generally follow the precedent set by prior rulings on similar facts, providing predictability, though a precedent can be overturned by a higher court or a sufficiently different set of facts.",
         capability_tags=["default to prior precedent for predictability", "precedent can be overridden by sufficient new facts"],
         mechanism_template="Default to a previously established decision for similar future cases, overriding it only when a higher authority or sufficiently different circumstances warrant it.",
         domain_terms=["stare decisis", "precedent", "common law"]),
    dict(id="agriculture_crop_rotation", domain="agriculture", title="Crop Rotation",
         text="Planting a different crop in a field each season, rather than the same crop repeatedly, replenishes soil nutrients that a single crop depletes and interrupts the life cycle of pests and diseases specific to that crop.",
         capability_tags=["rotate resource use to avoid depleting a shared pool", "interrupt a cycle by changing conditions periodically"],
         mechanism_template="Periodically vary which resource is drawn upon so no single resource is continuously depleted, which also interrupts cycles that depend on unchanging conditions.",
         domain_terms=["crop rotation", "soil depletion", "pest cycle"]),
    dict(id="textile_weaving_patterns", domain="textiles", title="Weave Patterns",
         text="A fabric's weave pattern, such as plain, twill, or satin, determines its strength, drape, and appearance by varying how the weft thread passes over and under successive warp threads.",
         capability_tags=["vary a repeating over-under pattern to change bulk properties"],
         mechanism_template="Vary a repeating local interleaving pattern to change the aggregate properties of the resulting structure.",
         domain_terms=["weave", "warp", "weft"]),
    dict(id="cryptography_one_time_pad", domain="cryptography", title="The One-Time Pad",
         text="A one-time pad achieves perfect secrecy by combining a message with a truly random key of the same length, used only once; reusing the key for a second message breaks the security guarantee entirely.",
         capability_tags=["combine with single-use randomness for a strong guarantee", "guarantee is void if the random material is reused"],
         mechanism_template="Combine a payload with single-use, never-reused randomness of matching size to achieve a strong guarantee that is voided entirely if the randomness is ever reused.",
         domain_terms=["one-time pad", "perfect secrecy", "key reuse"]),
]

for n in NOISE:
    add(domain=n["domain"], id=n["id"], title=n["title"], text=n["text"],
        capability_tags=n["capability_tags"], mechanism_template=n["mechanism_template"],
        domain_terms=n["domain_terms"], code_skeleton=None, is_distractor=False)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "knowledge_base.jsonl"
    save_cards(CARDS, out)
    domains = sorted(set(c.domain for c in CARDS))
    print(f"Wrote {len(CARDS)} cards to {out}")
    print(f"Domains ({len(domains)}): {domains}")
    print(f"Donor cards: {sum(1 for c in CARDS if c.code_skeleton and not c.is_distractor)}")
    print(f"Distractor cards: {sum(1 for c in CARDS if c.is_distractor)}")
    print(f"Noise cards: {sum(1 for c in CARDS if c.code_skeleton is None)}")
