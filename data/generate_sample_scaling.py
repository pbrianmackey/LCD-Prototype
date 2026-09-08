"""
Quick sample generator for scaling experimentation.
This shows what adding 20 new cards to 40 → 100 might look like.
Each entry includes research hints so you can fill in the real details.
"""

PROPOSED_NEW_CARDS = [
    {
        "id": "neuroscience_spike_timing",
        "domain": "neuroscience",
        "title": "Spike-Timing-Dependent Plasticity",
        "text": """RESEARCH NEEDED: Spike-timing-dependent plasticity (STDP) is a learning rule in neuroscience where the timing between presynaptic and postsynaptic spikes determines whether a synapse strengthens or weakens. If the presynaptic neuron fires shortly before the postsynaptic neuron, the synapse strengthens (long-term potentiation); if after, it weakens (long-term depression). This Hebbian-like rule, implemented locally at each synapse without global coordination, allows neural circuits to learn input-output associations. Key insight: tiny timing differences (milliseconds) determine learning direction.""",
        "capability_tags": [
            "strengthen synapses for inputs that precede desired outputs",
            "weaken synapses for inputs that follow desired outputs",
            "learn input-output associations via purely local temporal rules",
            "bidirectional learning: same mechanism can strengthen or weaken",
        ],
        "mechanism_template": "Given a synapse that receives repeated presynaptic and postsynaptic signals at varying relative timings, adjust synaptic weight based on the timing: increase weight if presynaptic precedes postsynaptic, decrease if postsynaptic precedes presynaptic. Over many repetitions, this tunes the synapse to fire preferentially for inputs that predict desired outputs.",
        "domain_terms": ["spike-timing-dependent plasticity", "STDP", "long-term potentiation", "long-term depression", "synapse", "Hebbian"],
        "code_skeleton": None,  # TODO: Implement if needed
        "is_distractor": False,
    },
    {
        "id": "finance_black_scholes",
        "domain": "finance",
        "title": "Black-Scholes Option Pricing",
        "text": """RESEARCH NEEDED: The Black-Scholes model prices European-style options by treating the underlying asset price as a stochastic process (geometric Brownian motion) and computing the expected payoff discounted to present value. The model requires: current price, strike price, time to expiration, risk-free rate, and volatility. Key insight: the option value depends on the *distribution* of future prices, not the expected price. The model captures this via a partial differential equation whose solution gives a closed-form formula. Despite its assumptions (no dividends, no transaction costs, log-normal returns), it's widely used and remarkably robust.""",
        "capability_tags": [
            "price a derivative by modeling the distribution of future outcomes",
            "capture uncertainty via a stochastic process model",
            "discount uncertain future payoff to present value",
            "adapt valuation when volatility or time to expiration changes",
        ],
        "mechanism_template": "Given an instrument whose value at expiration depends on a random future quantity, price it by: (1) model the random quantity as a stochastic process (e.g., geometric Brownian motion), (2) compute the expected payoff under the stochastic model, (3) discount to present value using the risk-free rate. The option value is sensitive to volatility and time remaining, not just the current price.",
        "domain_terms": ["Black-Scholes", "option pricing", "volatility", "geometric Brownian motion", "stochastic", "risk-free rate"],
        "code_skeleton": None,
        "is_distractor": False,
    },
    {
        "id": "climate_carbon_cycle",
        "domain": "climate_science",
        "title": "Carbon Cycle Feedback Loops",
        "text": """RESEARCH NEEDED: The global carbon cycle includes feedback loops: warmer air holds more water vapor (a greenhouse gas), which traps more heat, warming the air further (positive feedback). Conversely, more CO2 promotes plant growth, which pulls CO2 from the air (negative feedback). Permafrost thaw releases methane, amplifying warming. The net effect of these competing feedbacks determines climate sensitivity: how much the planet warms per unit of CO2 added. Key insight: understanding feedback loops—which amplify, which damp—is crucial for predicting long-term climate response.""",
        "capability_tags": [
            "model coupled feedback processes that amplify or damp each other",
            "distinguish positive (amplifying) from negative (dampening) feedback",
            "predict long-term system response given feedback structure",
            "recognize that a small initial change can trigger large responses via positive feedback",
        ],
        "mechanism_template": "Given a system with multiple coupled processes (e.g., CO2 ↔ temperature ↔ water vapor ↔ clouds), predict its long-term behavior by identifying feedback loops: does an increase in one quantity increase or decrease other quantities that feed back to amplify the original change? Model the feedback structure; positive feedbacks amplify changes, negative feedbacks damp them.",
        "domain_terms": ["carbon cycle", "feedback loop", "climate sensitivity", "permafrost", "methane", "greenhouse gas"],
        "code_skeleton": None,
        "is_distractor": False,
    },
    {
        "id": "botany_phyllotaxis",
        "domain": "botany",
        "title": "Phyllotaxis: Spiral Leaf Arrangement",
        "text": """RESEARCH NEEDED: Leaves on a plant stem often spiral upward at a consistent angle (the divergence angle). Many plants converge on the golden angle (~137.5°), which minimizes self-shading and maximizes light capture. This emerges from local rules: each new leaf grows at a fixed angle from the previous leaf, without any global plan. The pattern is governed by Fibonacci sequences and the golden ratio. Key insight: a globally optimal spatial arrangement emerges from purely local growth rules, without global coordination.""",
        "capability_tags": [
            "achieve globally optimal spatial packing via local growth rules",
            "converge on a consistent angle despite no global plan",
            "minimize overlap and waste (self-shading) through local geometry",
            "stable pattern emerges from repeated application of a simple rule",
        ],
        "mechanism_template": "Given items to be arranged sequentially in space where each item blocks resources (light) for subsequent items, arrange them by placing each new item at a fixed angle from the previous one. Over many iterations, this locally greedy rule produces a globally optimal packing that minimizes self-interference.",
        "domain_terms": ["phyllotaxis", "divergence angle", "golden angle", "Fibonacci", "self-shading"],
        "code_skeleton": None,
        "is_distractor": False,
    },
    {
        "id": "mineralogy_nucleation",
        "domain": "mineralogy",
        "title": "Crystal Nucleation Kinetics",
        "text": """RESEARCH NEEDED: Crystals don't form spontaneously; they require a nucleation event—a tiny seed crystal that grows. Nucleation is a phase transition with an activation barrier: creating the first few atomic layers is unfavorable (high energy), but once a nucleus is large enough, adding more layers is favorable. Temperature and supersaturation (how far from equilibrium) determine nucleation rate. Key insight: a system can be stuck in a metastable state (like supercooled water) until a random fluctuation triggers nucleation, then the transition proceeds rapidly.""",
        "capability_tags": [
            "transition from metastable state when a threshold is crossed",
            "require an initial seed or catalyst to begin a favored transition",
            "distinguish nucleation rate (initiation) from growth rate (propagation)",
            "recognize that local unfavorability early on enables global favorability later",
        ],
        "mechanism_template": "Given a system in a metastable state (stable locally but not globally), predict when it will transition: nucleation occurs when thermal noise or external perturbation crosses an activation barrier. Once nucleation begins, the new phase grows rapidly. The nucleation rate depends on temperature and how far from equilibrium the system is.",
        "domain_terms": ["nucleation", "crystal growth", "activation barrier", "metastable", "supersaturation", "phase transition"],
        "code_skeleton": None,
        "is_distractor": False,
    },
]

# Summary
print(f"Sample: {len(PROPOSED_NEW_CARDS)} new cross-domain donor cards")
for card in PROPOSED_NEW_CARDS:
    print(f"  - {card['domain']:20s}: {card['title']}")

print("\nTo scale to 100 cards:")
print("  1. Add 12 more cross-domain donors like these 5 samples")
print("  2. Add 12 same-field alternatives for each problem")
print("  3. Add refined distractors and realistic noise")
print("\nYou can then run:")
print("  python3 data/build_knowledge_base.py  # to regenerate knowledge_base.jsonl")
