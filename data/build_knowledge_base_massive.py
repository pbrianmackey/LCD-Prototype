"""
Generate massive knowledge bases via combinatorial expansion.

Strategy:
- Start with core donors and mechanisms
- Generate variants across multiple dimensions:
  * Notational variants (math, systems, CS, natural language)
  * Problem variants (same mechanism, different domain framing)
  * Mechanism variants (components, parameters, configurations)
  * Adversarial variants (mechanistically close, different vocabulary)
  * Noise/distractor variants (plausible but wrong)

Scale targets: 1K → 10K → 100K → 1M → 4M cards
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lcd.schema import KnowledgeCard, save_cards

def generate_massive_kb(target_size=1000):
    """
    Generate a knowledge base of target_size by expanding core cards.

    Scaling strategy:
    - 100 base donors
    - For each donor: generate N variants across dimensions
    - Total = 100 * expansion_factor
    """
    CARDS = []

    def add(**kw):
        CARDS.append(KnowledgeCard(**kw))

    # Core 100 donor mechanisms (from previous work)
    CORE_DONORS = [
        ("control_theory_pid", "control_theory", "PID Feedback Control",
         "A proportional-integral-derivative (PID) controller continuously computes an error value e(t) as the difference between a desired setpoint and a measured process variable, then applies a correction u(t) = Kp*e(t) + Ki*integral(e) + Kd*(de/dt). The proportional term reacts to the present error, the integral term eliminates residual steady-state offset by accumulating past error, and the derivative term damps the response by anticipating where the error is heading.",
         ["maintain target value", "corrective feedback", "proportional term", "integral term", "derivative term"],
         "Given a measured quantity, a target setpoint, and delayed actuation, maintain the target via corrective feedback using PID control.",
         ["PID", "control", "setpoint"],
         "lcd.mechanisms.pid.PIDController"),

        ("statistics_reservoir_sampling", "statistics", "Reservoir Sampling",
         "Reservoir sampling draws a uniform random sample of size k from a population of unknown size, seen only once, using O(k) memory. The first k items fill the reservoir. Each subsequent item i replaces a random slot with probability k/(i+1). This preserves uniform inclusion probability at every point.",
         ["sample from stream", "uniform distribution", "unknown size", "single pass"],
         "Given a stream of unknown length, maintain a k-sized uniform sample using O(k) memory.",
         ["reservoir", "sampling"],
         "lcd.mechanisms.reservoir_sampling.reservoir_sample"),

        ("logistics_elevator_scan", "operations_research", "SCAN / Elevator Servicing",
         "The SCAN algorithm services pending requests along a 1-D line by sweeping in one direction, picking up every request in path, then reversing. This minimizes travel distance and avoids backtracking.",
         ["sweep direction", "minimize travel", "avoid backtracking", "one-dimensional"],
         "Given requests on a 1-D line, minimize travel by sweeping monotonically then reversing.",
         ["SCAN", "elevator", "scheduling"],
         "lcd.mechanisms.scan_scheduling.scan_schedule"),

        ("statistical_physics_simulated_annealing", "statistical_physics", "Simulated Annealing",
         "Simulated annealing escapes local optima by accepting worse configurations with probability exp(-delta/T), where T decreases over time. High T allows exploration; low T accepts only improvements.",
         ["escape local optimum", "temperature schedule", "probabilistic acceptance", "exploration-exploitation"],
         "Given a combinatorial problem stuck in local optimum, search by accepting worse solutions with decreasing probability.",
         ["annealing", "temperature", "optimization"],
         "lcd.mechanisms.simulated_annealing.anneal"),
    ]

    # Add core donors
    for donor in CORE_DONORS:
        add(
            id=donor[0],
            domain=donor[1],
            title=donor[2],
            text=donor[3],
            capability_tags=donor[4],
            mechanism_template=donor[5],
            domain_terms=donor[6],
            code_skeleton=donor[7],
            is_distractor=False,
        )

    print(f"Added {len(CORE_DONORS)} core donors")

    # Calculate expansion factor needed
    current_size = len(CARDS)
    if target_size <= current_size:
        print(f"Target size {target_size} already reached with {current_size} cards")
        return CARDS

    cards_needed = target_size - current_size

    # === LAYER 1: Notational Variants ===
    # For each donor, create 3 variants: mathematical, systems, CS framing
    notational_variants = []
    variant_id = 0
    for donor in CORE_DONORS:
        base_id, domain, title = donor[0], donor[1], donor[2]
        for notation in ["mathematical", "systems", "cs"]:
            variant_id += 1
            notational_variants.append((
                f"{base_id}_v{notation}",
                domain,
                f"{title} ({notation.upper()} notation)",
                f"[{notation.upper()} FRAMING] {donor[3]} Represented using {notation} language and concepts.",
                donor[4],
                donor[5],
                donor[6],
                donor[7],
            ))

    # Add notational variants
    for variant in notational_variants:
        add(
            id=variant[0],
            domain=variant[1],
            title=variant[2],
            text=variant[3],
            capability_tags=variant[4],
            mechanism_template=variant[5],
            domain_terms=variant[6],
            code_skeleton=variant[7],
            is_distractor=False,
        )
    print(f"Added {len(notational_variants)} notational variants")

    # === LAYER 2: Problem Domain Variants ===
    # For each donor, express the same mechanism in 5 different application domains
    application_domains = [
        "robotics", "telecommunications", "finance", "biology", "manufacturing",
        "healthcare", "transportation", "energy", "agriculture", "urban_planning"
    ]

    problem_variants = []
    for donor in CORE_DONORS:
        base_id, title = donor[0], donor[2]
        for i, app_domain in enumerate(application_domains[:5]):  # 5 domains per donor
            problem_variants.append((
                f"{base_id}_domain{i}",
                app_domain,
                f"{title} in {app_domain.replace('_', ' ').title()}",
                f"[{app_domain.upper()}] {donor[3]} Applied to {app_domain} domain.",
                donor[4],
                donor[5],
                donor[6],
                donor[7],
            ))

    for variant in problem_variants:
        add(
            id=variant[0],
            domain=variant[1],
            title=variant[2],
            text=variant[3],
            capability_tags=variant[4],
            mechanism_template=variant[5],
            domain_terms=variant[6],
            code_skeleton=variant[7],
            is_distractor=False,
        )
    print(f"Added {len(problem_variants)} problem domain variants")

    # === LAYER 3: Mechanism Component Variants ===
    # For each donor, create variants with different parameters/configurations
    component_configs = [
        ("aggressive", "High-gain aggressive tuning"),
        ("conservative", "Low-gain conservative tuning"),
        ("balanced", "Medium-gain balanced tuning"),
        ("adaptive", "Adaptive parameter tuning"),
        ("robust", "Robust to disturbances"),
    ]

    mechanism_variants = []
    for donor in CORE_DONORS:
        base_id, domain, title = donor[0], donor[1], donor[2]
        for config_name, config_desc in component_configs:
            mechanism_variants.append((
                f"{base_id}_config_{config_name}",
                domain,
                f"{title} ({config_name})",
                f"[{config_name.upper()}] {donor[3]} Configured for {config_desc}.",
                donor[4],
                donor[5],
                donor[6],
                donor[7],
            ))

    for variant in mechanism_variants:
        add(
            id=variant[0],
            domain=variant[1],
            title=variant[2],
            text=variant[3],
            capability_tags=variant[4],
            mechanism_template=variant[5],
            domain_terms=variant[6],
            code_skeleton=variant[7],
            is_distractor=False,
        )
    print(f"Added {len(mechanism_variants)} mechanism configuration variants")

    # === LAYER 4: Hybrid/Composite Mechanisms ===
    # Blend two mechanisms together
    hybrid_cards = []
    for i, donor1 in enumerate(CORE_DONORS):
        for j, donor2 in enumerate(CORE_DONORS):
            if i < j:  # Avoid duplicates
                hybrid_id = f"hybrid_{donor1[0][:8]}_{donor2[0][:8]}"
                hybrid_cards.append((
                    hybrid_id,
                    "computer_science",
                    f"Hybrid: {donor1[2]} + {donor2[2]}",
                    f"Combines {donor1[2]} with {donor2[2]} for improved robustness.",
                    donor1[4] + donor2[4][:2],
                    f"{donor1[5]} and {donor2[5]}",
                    list(set(donor1[6] + donor2[6])),
                    donor1[7],
                ))

    for variant in hybrid_cards:
        add(
            id=variant[0],
            domain=variant[1],
            title=variant[2],
            text=variant[3],
            capability_tags=variant[4],
            mechanism_template=variant[5],
            domain_terms=variant[6],
            code_skeleton=variant[7],
            is_distractor=False,
        )
    print(f"Added {len(hybrid_cards)} hybrid/composite mechanisms")

    # === LAYER 5: Distractors (same-field alternatives) ===
    # Generate plausible but mechanistically wrong alternatives
    distractor_patterns = [
        ("threshold_based", "Threshold-based approach"),
        ("greedy_nearest", "Greedy nearest-first heuristic"),
        ("round_robin", "Round-robin allocation"),
        ("random_selection", "Randomized selection"),
        ("first_come_first_served", "First-come-first-served"),
        ("priority_queue", "Fixed priority ordering"),
        ("load_balanced", "Simple load balancing"),
        ("cached_results", "Cached lookup table"),
    ]

    distractors = []
    for donor in CORE_DONORS:
        base_id = donor[0]
        for pattern_name, pattern_desc in distractor_patterns:
            distractors.append((
                f"{base_id}_distract_{pattern_name}",
                "software_engineering",
                f"Alternative: {pattern_desc}",
                f"A plausible alternative to {donor[2]}: {pattern_desc}. This approach is simpler but mechanistically different.",
                ["alternative approach", "simpler heuristic"],
                f"Use {pattern_desc} instead of the optimal mechanism.",
                [pattern_name, base_id],
                None,
            ))

    for variant in distractors:
        add(
            id=variant[0],
            domain=variant[1],
            title=variant[2],
            text=variant[3],
            capability_tags=variant[4],
            mechanism_template=variant[5],
            domain_terms=variant[6],
            code_skeleton=variant[7],
            is_distractor=True,
        )
    print(f"Added {len(distractors)} distractor cards")

    # === LAYER 6: Noise Cards (if needed) ===
    # Generate unrelated noise to reach target size
    noise_domains = [
        "art", "music", "literature", "history", "philosophy",
        "sports", "cuisine", "fashion", "architecture", "linguistics",
        "astronomy", "geology", "meteorology", "oceanography", "ecology",
    ]

    current_size = len(CARDS)
    noise_count = max(0, target_size - current_size)

    for i in range(noise_count):
        domain_idx = i % len(noise_domains)
        domain = noise_domains[domain_idx]
        add(
            id=f"noise_{i:06d}",
            domain=domain,
            title=f"Random Concept {i}",
            text=f"This is a noise card from domain {domain} with index {i}. It is unrelated to mechanism-based problems.",
            capability_tags=["unrelated", f"domain_{domain}"],
            mechanism_template="Unrelated noise card.",
            domain_terms=[domain, f"noise_{i}"],
            code_skeleton=None,
            is_distractor=False,
        )

    print(f"Added {noise_count} noise cards")
    print(f"Total cards: {len(CARDS)}")

    return CARDS


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate massive knowledge bases")
    parser.add_argument("--size", type=int, default=1000, help="Target KB size (default 1000)")
    parser.add_argument("--output", type=str, default=None, help="Output file (default: data/knowledge_base_N.jsonl)")
    args = parser.parse_args()

    print(f"Generating KB with target size: {args.size}")
    print("="*70)

    cards = generate_massive_kb(target_size=args.size)

    output = args.output or f"data/knowledge_base_{args.size}.jsonl"
    out_path = Path(output)
    save_cards(cards, out_path)

    domains = sorted(set(c.domain for c in cards))
    donors = sum(1 for c in cards if c.code_skeleton and not c.is_distractor)
    distractors = sum(1 for c in cards if c.is_distractor)
    noise = sum(1 for c in cards if c.code_skeleton is None and not c.is_distractor)

    print(f"\n{'='*70}")
    print(f"Wrote {len(cards)} cards to {out_path}")
    print(f"Unique domains: {len(domains)}")
    print(f"  Donor cards: {donors}")
    print(f"  Distractor cards: {distractors}")
    print(f"  Noise cards: {noise}")
    print(f"Domains: {', '.join(domains[:10])}..." if len(domains) > 10 else f"Domains: {', '.join(domains)}")
