"""
Authors benchmark/benchmark.jsonl -- the 14 BenchmarkProblem records.

Every `statement` is written as a domain-neutral software-engineering problem
description. None of them name the donor mechanism's jargon (no "PID",
"reservoir sampling", "SIR model", "pheromone", etc.) -- see each card's
`domain_terms` list in data/build_knowledge_base.py for exactly which words
are being avoided. This is what stands in for the historical benchmark's
"corpus cutoff before the discovery date" (spec section 8): the problem
statement itself contains no lexical trace of the intended donor field.

`donor_card_id` and `baseline_a_card_id` are recorded for scoring only. They
are never read by either retriever (see lcd/retriever.py) -- retrieval sees
only `statement` text and KnowledgeCard text/capability fields.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lcd.schema import BenchmarkProblem, save_problems

PROBLEMS = [
    BenchmarkProblem(
        id="autoscaler_oscillation",
        title="Worker pool keeps overshooting during load spikes",
        statement=(
            "Our worker pool autoscaler keeps overshooting. When request volume spikes, the "
            "autoscaler adds workers, but there's a delay before new workers actually come "
            "online and affect the backlog. By the time they kick in, the backlog has already "
            "swung past the target, so the autoscaler yanks capacity back out, overshoots the "
            "other way, and the backlog oscillates around the target instead of settling down. "
            "We need an autoscaling rule that adjusts capacity smoothly and settles near a "
            "target backlog length despite a sudden load spike and a lag between a capacity "
            "decision and its effect on the backlog."
        ),
        donor_card_id="control_theory_pid",
        baseline_a_card_id="se_threshold_autoscaling",
        harness_module="benchmark.problems.autoscaler_oscillation",
        historical_note=("Real-world parallel: PID and lead-lag compensators are the standard "
                          "fix for oscillating control loops with actuation delay, in domains "
                          "from thermostats to cruise control."),
    ),
    BenchmarkProblem(
        id="streaming_sample",
        title="Uniform sample from a log source too large to hold in memory",
        statement=(
            "We need to draw a uniformly random sample of a few hundred records from a log "
            "source for spot-checking. The source can only be read once, forward, like a "
            "stream -- we don't know its total length in advance and can't seek backward or "
            "re-read it. It's also too large to comfortably hold in memory all at once. "
            "Produce a uniformly random sample of a fixed size k from such a source without "
            "materializing the whole thing."
        ),
        donor_card_id="statistics_reservoir_sampling",
        baseline_a_card_id="se_materialize_then_sample",
        harness_module="benchmark.problems.streaming_sample",
        historical_note=("Real-world parallel: reservoir sampling (Vitter 1985) is the "
                          "standard statistics answer to sampling from an unbounded stream."),
    ),
    BenchmarkProblem(
        id="warehouse_robot_picking",
        title="Picking robot travels too far on a single long aisle",
        statement=(
            "A picking robot moves along a single long storage aisle to visit a fixed set of "
            "pick locations (given as distances in feet from a dock position, some ahead, some "
            "behind). It currently just drives to whichever pending pick location is closest "
            "at each moment, but ends up crisscrossing the aisle far more than seems necessary "
            "and its total travel distance is much higher than we'd like. Devise a dispatch "
            "rule for visiting all pending locations that minimizes total distance traveled "
            "along the aisle."
        ),
        donor_card_id="logistics_elevator_scan",
        baseline_a_card_id="se_nearest_neighbor_dispatch",
        harness_module="benchmark.problems.warehouse_robot_picking",
        historical_note="",
    ),
    BenchmarkProblem(
        id="server_bin_packing",
        title="Job-to-server assignment stuck well above the best possible balance",
        statement=(
            "We assign a batch of jobs, each with a known fixed cost, onto a small fixed number "
            "of servers, and want to minimize the maximum load on any one server. Our current "
            "approach sorts jobs largest-first and always places the next job on whichever "
            "server currently has the least load. On one particular job batch this produces a "
            "noticeably worse balance than we believe should be achievable. Find an assignment "
            "approach that can do better than always committing greedily to the "
            "currently-best-looking placement."
        ),
        donor_card_id="statistical_physics_simulated_annealing",
        baseline_a_card_id="se_first_fit_decreasing",
        harness_module="benchmark.problems.server_bin_packing",
        historical_note="",
    ),
    BenchmarkProblem(
        id="replication_broadcast",
        title="Update never reaches most nodes in a sparsely connected cluster",
        statement=(
            "We need to propagate a write from one origin node to as many of the other nodes "
            "in a cluster as possible. The cluster isn't fully connected -- each node only has "
            "direct links to a handful of others -- and on any given attempt a node has some "
            "chance of being temporarily unreachable. Our current approach has the origin push "
            "the update directly to its own directly-connected neighbors in one shot, with no "
            "retry and no relaying by anyone else, so most of the cluster never gets the "
            "update at all. Design a propagation approach that reaches nearly all nodes despite "
            "sparse connectivity and random per-attempt unreachability, with no central "
            "coordinator directing the whole process."
        ),
        donor_card_id="epidemiology_sir_gossip",
        baseline_a_card_id="se_central_fanout_broadcast",
        harness_module="benchmark.problems.replication_broadcast",
        historical_note=("Real-world parallel: 'epidemic algorithms' for replicated database "
                          "maintenance (Demers et al., 1987) explicitly borrowed compartmental "
                          "epidemic-spread models from epidemiology; the underlying epidemic "
                          "math is far older."),
    ),
    BenchmarkProblem(
        id="network_load_diffusion",
        title="One overloaded server, no global view available to rebalance it",
        statement=(
            "One server in a network of peers has become overloaded while the rest sit mostly "
            "idle. Servers can only exchange load information and work with their own direct "
            "neighbors in the network -- there's no central coordinator and no server has a "
            "global view of everyone's load. Right now load simply never moves once assigned. "
            "Design a way for the network to even out an extreme load imbalance over time using "
            "only repeated local, neighbor-to-neighbor exchanges."
        ),
        donor_card_id="physics_heat_diffusion",
        baseline_a_card_id="se_no_rebalancing",
        harness_module="benchmark.problems.network_load_diffusion",
        historical_note="",
    ),
    BenchmarkProblem(
        id="starvation_free_scheduling",
        title="An important task never gets scheduled behind a flood of routine work",
        statement=(
            "One important task enters our task queue alongside a continuous, never-ending "
            "flood of routine tasks that individually carry higher fixed priority than the "
            "important task. Our scheduler always runs the strictly-highest-priority ready "
            "task, so the important task never runs at all -- there's always a fresh routine "
            "task with higher priority ready to go. Design a scheduling rule that guarantees "
            "every task, including lower-priority ones, gets served within a bounded amount of "
            "time, while still generally favoring higher-value work."
        ),
        donor_card_id="economics_congestion_pricing_aging",
        baseline_a_card_id="se_strict_priority_queue",
        harness_module="benchmark.problems.starvation_free_scheduling",
        historical_note=("Real-world parallel: priority aging in OS schedulers and congestion "
                          "pricing / Vickrey auctions in market design solve the same shape of "
                          "problem independently."),
    ),
    BenchmarkProblem(
        id="adaptive_routing",
        title="Cached route stays fast on paper long after conditions change",
        statement=(
            "Traffic between two points can take one of several routes, and route costs change "
            "over time as conditions shift. Our router computes the cheapest route once, from "
            "a snapshot of conditions, and caches that choice forever. When conditions later "
            "shift so a previously-cheap route becomes expensive and another becomes cheap, the "
            "router keeps sending traffic down the now-expensive route because it never "
            "revisits its choice. Design a routing approach that keeps adapting to shifting "
            "route costs over many repeated trips, without recomputing a full global "
            "recalculation from scratch on every single trip."
        ),
        donor_card_id="entomology_ant_colony",
        baseline_a_card_id="se_static_shortest_path",
        harness_module="benchmark.problems.adaptive_routing",
        historical_note=("Real-world parallel: Ant Colony Optimization (Dorigo, early 1990s) "
                          "applied real ant foraging behavior to network routing and other "
                          "combinatorial problems."),
    ),
    BenchmarkProblem(
        id="anomaly_detection_no_labels",
        title="Outlier detector can't see anomalies that look normal in aggregate",
        statement=(
            "We want to flag anomalous system states, but we only have examples of normal "
            "states to work from -- no labeled examples of what an anomaly looks like. Our "
            "current approach reduces each state to a single summary number and flags states "
            "whose number is statistically unusual relative to normal examples. In practice, "
            "some real anomalies have a summary number indistinguishable from normal states "
            "(same count of active indicators, just arranged differently), so this approach "
            "never flags them. Design a detection approach, trainable on normal examples alone, "
            "that can catch anomalies that are structurally different from normal even when a "
            "simple summary statistic looks identical."
        ),
        donor_card_id="immunology_negative_selection",
        baseline_a_card_id="se_zscore_outlier",
        harness_module="benchmark.problems.anomaly_detection_no_labels",
        historical_note=("Real-world parallel: 'artificial immune systems' for intrusion/anomaly "
                          "detection (Forrest et al., 1994) directly adapted negative selection "
                          "from immunology."),
    ),
    BenchmarkProblem(
        id="producer_consumer_oscillation",
        title="Worker pool and backlog stuck in a boom-bust cycle",
        statement=(
            "A worker pool scales reactively against a backlog: workers are added in "
            "proportion to how much backlog and worker interaction is currently happening, and "
            "the backlog shrinks in proportion to that same interaction, while also growing on "
            "its own at a steady base rate. With this purely reactive rule the system falls "
            "into a large, sustained boom-bust cycle -- backlog and worker count both swing "
            "wildly and never settle. Modify the scaling rule so the system settles toward a "
            "stable equilibrium instead of cycling indefinitely."
        ),
        donor_card_id="ecology_predator_prey_damping",
        baseline_a_card_id="se_reactive_worker_step",
        harness_module="benchmark.problems.producer_consumer_oscillation",
        historical_note="",
    ),
    BenchmarkProblem(
        id="admission_control_congestion_collapse",
        title="Throughput collapses to near zero exactly when load is highest",
        statement=(
            "Our backend can sustainably process about 10 requests per tick. During a traffic "
            "spike offering far more than that, we currently admit every request immediately "
            "and let the backend itself absorb the overload. Under this policy, completed "
            "throughput during the spike actually collapses toward zero -- worse than doing "
            "nothing -- because contention among too many concurrently in-flight requests "
            "wastes more capacity the more of them there are. Design an admission approach that "
            "keeps completed throughput near capacity during a large overload spike, rather "
            "than collapsing."
        ),
        donor_card_id="transportation_ramp_metering",
        baseline_a_card_id="se_admit_all_retry",
        harness_module="benchmark.problems.admission_control_congestion_collapse",
        historical_note=("Real-world parallel: TCP congestion control and highway ramp "
                          "metering both address the same 'capacity drop under overload' "
                          "phenomenon, independently, in software and transportation "
                          "engineering."),
    ),
    BenchmarkProblem(
        id="stale_value_consensus",
        title="Conflict resolution keeps picking the wrong replica's value",
        statement=(
            "Several replicas can independently report a value for the same key, and reports "
            "can arrive out of order due to network delay -- a replica that has been holding a "
            "stale, minority value can end up with a newer-looking timestamp than replicas "
            "holding the correct, majority-held value. Our current conflict resolution always "
            "keeps whichever report has the most recent timestamp, which means it sometimes "
            "picks the stale minority value over the value most replicas actually hold. Design "
            "a conflict-resolution rule that is robust to a minority of replicas reporting late "
            "or stale values."
        ),
        donor_card_id="social_choice_quorum_voting",
        baseline_a_card_id="se_last_write_wins",
        harness_module="benchmark.problems.stale_value_consensus",
        historical_note=("Real-world parallel: quorum-based agreement in distributed consensus "
                          "protocols (e.g. Paxos, Raft) mirrors majority-rule voting theory."),
    ),
    BenchmarkProblem(
        id="naive_sufficient_lookup",
        title="Look up values in a large, static, sorted configuration list",
        statement=(
            "We need to repeatedly check whether specific values are present in a large, "
            "mostly-static, sorted list of about 100,000 configuration entries, and want each "
            "lookup to be fast -- on the order of a few dozen comparisons at most, not "
            "thousands. Recommend a lookup approach that keeps per-query comparisons small on "
            "a large sorted list."
        ),
        donor_card_id="cs_binary_search",
        baseline_a_card_id="cs_binary_search",
        harness_module="benchmark.problems.naive_sufficient_lookup",
        control_type="naive_sufficient",
        historical_note="Control problem: same-domain knowledge (binary search) already suffices; no cross-domain reach should be needed or rewarded here.",
    ),
    BenchmarkProblem(
        id="impossible_sort_probe",
        title="Sort a list using far fewer comparisons than seems achievable",
        statement=(
            "We need to fully sort a list of 50 arbitrary, distinct, comparable values using "
            "at most 50 comparisons in total, i.e. no more comparisons than there are items. "
            "Find a comparison-based approach that reliably sorts arbitrary input within that "
            "comparison budget."
        ),
        donor_card_id="NONE",
        baseline_a_card_id="cs_binary_search",
        harness_module="benchmark.problems.impossible_sort_probe",
        control_type="no_kb_solution",
        historical_note=("Control problem: information-theoretically impossible for arbitrary "
                          "input (comparison sorting needs Omega(n log n) comparisons in the "
                          "worst case). Nothing in the knowledge base should pass; the system "
                          "should report failure rather than a false positive."),
    ),
]

if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "benchmark.jsonl"
    save_problems(PROBLEMS, out)
    print(f"Wrote {len(PROBLEMS)} problems to {out}")
    controls = [p.id for p in PROBLEMS if p.control_type]
    print(f"Control problems: {controls}")
