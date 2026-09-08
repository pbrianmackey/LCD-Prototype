# Latent Capability Discovery — Prototype (v0.1)

This is a runnable prototype and small end-to-end experiment testing one question: does explicitly decomposing knowledge into domain-neutral, transferable "capabilities" — and retrieving by capability match rather than by topic/text similarity — find cross-domain problem-solving mechanisms that ordinary RAG misses?

The short answer from this prototype: yes, with one clean, explicable exception. At a fixed, realistic retrieval budget (5 attempts), a capability-based retriever paired with a convergence loop solved 11 of 12 cross-domain transfer problems (92%), against 9 of 12 (75%) for text-similarity RAG given the identical budget and convergence mechanism, and 0 of 12 for either a same-domain-only baseline or single-shot RAG. The capability-based approach also reached its answers using fewer attempts on average (2.07 vs 3.21). Full numbers, per-problem detail, and the sensitivity analysis are in `FINDINGS.md`.

## Quick start

```bash
pip install numpy scikit-learn matplotlib pytest   # scikit-learn/matplotlib/pytest if not already present
python3 data/build_knowledge_base.py                # writes data/knowledge_base.jsonl (40 cards)
python3 benchmark/build_benchmark.py                # writes benchmark/benchmark.jsonl (14 problems)
python3 experiments/run_benchmark.py                # runs all 5 conditions, writes results/*.json
python3 experiments/sensitivity_sweep.py             # budget sensitivity, writes results/sensitivity_sweep.json
python3 experiments/analyze_results.py               # writes results/chart_*.png
python3 -m pytest tests/ -q                          # unit tests on the mechanism library and pipeline
python3 demo.py autoscaler_oscillation               # narrated single-problem walk through all 6 stages
```

Every problem module is also directly runnable, e.g. `python3 benchmark/problems/autoscaler_oscillation.py`, and prints PASS/FAIL for its donor mechanism and its same-domain distractor. `python3 experiments/diagnose_server_bin_packing.py` reproduces the one diagnosed miss discussed in `FINDINGS.md`.

## What's actually being tested

The research hypothesis (see the original spec this implements) is that some problems look unsolved not because the necessary knowledge doesn't exist, but because it's filed under the wrong label — a mechanism that would solve problem P sits in a knowledge base tagged by a field that has nothing obviously to do with P, so ordinary "search by topic similarity" retrieval never surfaces it. The fix proposed is to represent both problems and knowledge in terms of domain-neutral *capabilities* (what a technique actually does, mechanically) instead of the *field* it happens to be filed under, and retrieve by capability match.

This prototype operationalizes that as directly as possible:

- A 40-card knowledge base (`data/knowledge_base.jsonl`) spans 28 fields: 12 genuine cross-domain donor cards (control theory, statistics, epidemiology, physics, economics, entomology, immunology, ecology, transportation engineering, social choice theory, operations research, plus one same-domain CS card), 13 same-domain "software engineering" distractor cards that are topically on-point but mechanistically insufficient, and 14 cards from unrelated fields (cooking, music, geology, law, textiles, etc.) that solve nothing — pure retrieval noise.
- 14 benchmark problems (`benchmark/benchmark.jsonl`), all framed as ordinary software engineering problems in plain language, with the donor field's jargon deliberately absent from the problem text (checked automatically — see "Leakage check" in `experiments/run_benchmark.py`).
- Two retrievers over the *same* underlying TF-IDF vector space (`lcd/vectorspace.py`, `lcd/retriever.py`): one compares raw problem text to raw card text (ordinary RAG), the other projects both problem and card text through a fixed, hand-authored, 45-phrase domain-neutral "capability glossary" (`lcd/ontology.py`) and compares in that projected space, never reading either the problem's or the card's field label.
- An objective Critic: every problem is a runnable simulation or computation with a pass/fail test that was calibrated (not merely asserted) to separate the donor mechanism from the same-domain default — see `benchmark/problems/*.py`, each independently runnable and self-verifying.

## Running example

`autoscaler_oscillation`: a worker-pool autoscaler overshoots and oscillates under a load spike because of lag between a capacity decision and its effect on the backlog. The problem statement never mentions control theory. Text-similarity RAG's top candidate is a same-domain "reactive worker step" card (textually on-point: workers, backlog, scaling) which fails the oscillation test; the true fix — a PID controller, donor field control theory — ranks 9th out of 40 by raw text similarity and is never reached within a 5-attempt budget. The capability retriever, projecting through phrases like "avoiding oscillation by damping a control response," ranks the PID card 2nd and the pipeline finds it on its second attempt.

## Architecture

```
PROBLEM
   |
   v
1. DECOMPOSER          lcd/reasoner.py: Reasoner.decompose() -- top capability-glossary
   |                    axes the problem projects onto (human-readable trace only)
   v
2. CAPABILITY SEARCH    lcd/retriever.py: rag_retrieve() / capability_retrieve()
   |                    -- the one thing that differs between conditions
   v
3. ABSTRACTOR           lcd/reasoner.py: Reasoner.abstract() -- strips card.domain_terms,
   |                    surfaces card.mechanism_template (trace + Reconstructor input)
   v
4. RECONSTRUCTOR        lcd/pipeline.py: Reconstructor.build() -- selects + invokes the
   |                    card's code_skeleton, adapted to the problem's interface
   v
5. CRITIC / VALIDATOR   lcd/pipeline.py: Critic.judge() -- runs the problem's real
   |                    simulation/test. Objective pass/fail, no LLM judgment.
   |
 reject <----> candidate
   |               |
   v               v
 next card    record success
   |               |
   +-------+-------+
           v
6. CONVERGENCE         lcd/pipeline.py: Orchestrator.run() -- walks the ranked list until
                       a pass or a fixed attempt budget is exhausted
```

`lcd/pipeline.py`'s `Orchestrator` wires all six stages together and exposes five conditions (`CONDITIONS` in that file), which is how this prototype turns the architecture into an experiment rather than just a system:

| condition | retrieval | attempts | what it represents |
|---|---|---|---|
| `baseline_a_naive` | none | 1 (fixed card) | competent same-domain default, no retrieval at all |
| `rag_top1` | text similarity | 1 | ordinary RAG, single shot |
| `rag_convergence` | text similarity | up to 5 | ordinary RAG, given retries |
| `lcd_top1` | capability match | 1 | ablation: capability retrieval without the convergence loop |
| `lcd_convergence` | capability match | up to 5 | full Latent Capability Discovery |

## Design choices and where this simplifies the spec

Being upfront about these matters more than the numbers above, so they're listed here rather than buried.

**The Reasoner is heuristic, not an LLM, by default.** `lcd/reasoner.py` defines a `Reasoner` interface (`decompose`, `abstract`, `explain_transfer`) with a deterministic `HeuristicReasoner` as the default implementation and an optional `AnthropicReasoner` that activates only if `anthropic` and `ANTHROPIC_API_KEY` are present (it defaults to an Improving-IT-approved model string and is not used in the reported experiment). This was a deliberate choice, not a shortcut taken only for convenience: the research question here is specifically about *retrieval representation* (capability space vs. text space), and holding the reasoning engine fixed and deterministic isolates that variable. It also makes the whole experiment free, fast, and exactly reproducible. The cost is real: the Reasoner's `decompose`/`abstract` output in this prototype only populates a human-readable trace (why a card was attempted) — it does not, itself, decide which card gets tried or judge whether a candidate works. A production version would use an LLM here and would plausibly do better at exactly the case this prototype misses (see Limitations).

**The Reconstructor selects and invokes; it does not synthesize code.** Section 4 of the spec envisions an LLM writing the actual bridge from an abstracted mechanism to the specific problem. Building that generally would mean building a code-generating agent, which is a different (much larger) project and would re-introduce an LLM's raw capability as a confound in exactly the experiment this prototype is trying to run cleanly. Instead, each of the 12 cross-domain mechanisms is implemented once, generically, in `lcd/mechanisms/` (e.g. a real, general-purpose `PIDController`, a real `reservoir_sample`, a real `AntColonyRouter`), and each benchmark problem wires the specific cards it can meaningfully use to a factory function (`CARD_ADAPTERS` in each `benchmark/problems/*.py`). A card retrieved with no wired adapter is correctly treated as "not applicable" and fails the Critic rather than crashing — this is what happens on `impossible_sort_probe` regardless of condition, and is the mechanism behind the false-positive-safety result below.

**Retrieval is TF-IDF, not a neural embedding model or an LLM.** `lcd/vectorspace.py` fits one `TfidfVectorizer` over the union of all card text, all card capability text, all problem statements, and the 45 glossary phrases, and both retrievers are cosine similarity in that shared space — differing only in which fields get compared (see that file's docstring). This is a deliberately minimal, fully offline, dependency-light choice appropriate for a ~40-document knowledge base. It is also, per the one miss below, a real limitation: TF-IDF is lexical, not semantic, and a genuine word-overlap confound is diagnosed and left unfixed on purpose (see Limitations).

**The capability glossary is hand-authored, not learned.** The 45 phrases in `lcd/ontology.py` were written once, before any benchmark problem was authored, and never edited afterward to chase a result. Section 3 of the spec explicitly flags that "eventually we don't even want humans deciding the dimensions" as the further-out goal; a hand-authored-but-fixed ontology is the honest v0.1 step before that, and is exactly what's shipped here.

**No true historical, corpus-cutoff benchmark was built.** Section 8 of the spec calls for a benchmark of real historical discoveries with the corpus truncated before the discovery date. Building that rigorously needs a large, reliably dated corpus this prototype doesn't have access to. Instead, the 14 synthetic problems are the primary evaluated benchmark (this also sidesteps the memorization risk flagged in section 11 — none of these problems or their solutions can be recalled from training data, because they were constructed for this prototype), and where a synthetic problem happens to mirror a documented real transfer (gossip protocols from epidemiology, ant colony optimization from entomology, ramp metering/TCP congestion control, aging schedulers from congestion pricing), that's noted in `historical_note` fields in `benchmark/build_benchmark.py` as context, not claimed as a validated historical experiment.

**Scale.** 40 cards and 14 problems, chosen deliberately over a larger but shallower benchmark, per this project's brief to prioritize a small, real, end-to-end experiment over a large theoretical one. See `FINDINGS.md` for what a larger version would need.

## Repository layout

`lcd/` is the reusable library: `ontology.py` (capability glossary), `schema.py` (data model + JSONL I/O), `vectorspace.py` (shared TF-IDF space), `retriever.py` (the two retrievers), `reasoner.py` (Reasoner interface + implementations), `pipeline.py` (Decomposer/Reconstructor/Critic/Orchestrator), `metrics.py` (LDR and friends), `mechanisms/` (the 12 generic cross-domain mechanism implementations plus the same-domain naive baselines).

`data/build_knowledge_base.py` authors the 40 knowledge cards into `data/knowledge_base.jsonl`. `benchmark/build_benchmark.py` authors the 14 problems into `benchmark/benchmark.jsonl`; `benchmark/problems/*.py` are the executable simulations/tests. `experiments/` runs the benchmark, the budget sensitivity sweep, and produces charts. `results/` holds the actual output of the last run (raw per-attempt records, summary JSON, sensitivity sweep, charts) — nothing in this repo's reported numbers is hand-typed; `FINDINGS.md` was written from these files. `tests/` are conventional unit tests on the mechanism library and pipeline plumbing.

## Falsification

The brief this implements is explicit that a negative result is a legitimate outcome, and specifies what would count as one: ordinary RAG matching capability-based retrieval, or explicit decomposition actively hurting performance. Neither happened here, but the results aren't uniformly positive either, which is what makes them worth trusting: `lcd_top1` (capability retrieval with no convergence loop) only reaches 50%, meaningfully below `rag_convergence`'s 75% — the convergence loop, not the capability representation alone, is doing real work, and a capability-only system without retries would have looked mediocre. And `server_bin_packing` is a genuine, diagnosed miss for the full LCD condition at the reported budget: the simulated-annealing donor card ranks 10th in capability space because two unrelated cards (an admission-control distractor, a visual-composition noise card) happen to share incidental vocabulary with the problem statement in the 45-phrase projection. That's a real weakness of TF-IDF-based capability projection, left in rather than patched, because patching it after seeing the result would defeat the point of reporting it. See `FINDINGS.md` for the full breakdown, including the budget-sensitivity curve showing that both retrievers reach 100% given a large enough attempt budget — the finding is about efficiency and small-budget success rate, not about RAG being fundamentally incapable.

## Independent verification

Beyond the calibration tests in `tests/` and the honest-reporting discipline described above, this prototype's numbers and code were separately checked by an independent review pass (a fresh agent with no visibility into the design process, asked to reproduce the results from scratch, hunt for rigged thresholds or leaked answers, and verify the domain-blind retrieval claim by reading the code directly). It reproduced every reported number exactly, found no rigging or leakage, and confirmed `capability_retrieve` never reads a card's domain — but flagged one real gap, since folded into `FINDINGS.md`'s Limitations: roughly half of the 12 "cross-domain" donor mechanisms (quorum voting, SCAN scheduling, admission-control aging) have close analogs already standard within CS/distributed-systems curricula, so the "required reaching outside the field" framing is stronger for the other half (PID control, reservoir sampling, ant colony routing, negative selection, epidemic gossip, heat diffusion, predator-prey damping) than for all twelve uniformly.

## Extending this

Swap `HeuristicReasoner` for `AnthropicReasoner` (`lcd/reasoner.py`) once code synthesis in the Reconstructor is worth tackling. Replace the TF-IDF `VectorSpace` with a real sentence-embedding model to test whether the `server_bin_packing` miss is TF-IDF-specific. Grow the knowledge base past 40 cards and the benchmark past 14 problems — the harness in `experiments/run_benchmark.py` doesn't assume either size. Attempt a genuinely dated historical benchmark if a suitable corpus becomes available. Replace the hand-authored glossary with one learned from clustering card texts, per the spec's own long-run goal.
