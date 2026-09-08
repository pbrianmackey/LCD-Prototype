# Findings

All numbers below come from `results/summary.json`, `results/raw_results.json`, and `results/sensitivity_sweep.json`, produced by actually running `experiments/run_benchmark.py` and `experiments/sensitivity_sweep.py` against the 40-card knowledge base and 14-problem benchmark in this repository. Nothing here is hand-typed or illustrative; re-running the three commands in the README regenerates these files from scratch (the mechanisms and simulations are deterministic given fixed seeds, so the numbers reproduce exactly).

## Headline result

At a fixed convergence-attempt budget of 5:

| condition | LDR (12 core problems) | mean attempts used | cross-domain share of wins |
|---|---|---|---|
| A. same-domain naive, no retrieval | 0% (0/12) | 1.00 | — |
| B. text-similarity RAG, top-1 | 0% (0/12) | 1.00 | — |
| C. text-similarity RAG + convergence | 75% (9/12) | 3.21 | 100% |
| D. capability retrieval, top-1 (no convergence) | 50% (6/12) | 1.00 | 100% |
| E. full Latent Capability Discovery | **92% (11/12)** | **2.07** | 100% |

("Core problems" excludes the two control problems, reported separately below.) See `results/chart_ldr_by_condition.png`.

Full LCD (E) beats ordinary RAG with the identical convergence mechanism and budget (C) by 17 points of LDR while using about a third fewer attempts per problem on average. Neither same-domain knowledge alone (A) nor single-shot RAG (B) solves a single one of the 12 problems — by construction, every one of these problems needs a mechanism from outside the field the problem is nominally in, and the discriminating test in each problem was calibrated (not merely asserted) to confirm the same-domain default genuinely fails it and the cross-domain donor genuinely passes it (every problem module in `benchmark/problems/` is independently runnable and prints both outcomes).

## Retrieval rank: where the donor mechanism actually sits

This is the more direct test of the core hypothesis, independent of any pass/fail threshold: does projecting through the capability glossary move the correct cross-domain mechanism up the ranked list, relative to raw text similarity?

| problem | donor field | rank by text similarity (RAG) | rank by capability match (LCD) |
|---|---|---|---|
| autoscaler_oscillation | control theory | 9 | 2 |
| streaming_sample | statistics | 1 | 0 |
| warehouse_robot_picking | operations research | 2 | 0 |
| server_bin_packing | statistical physics | 7 | 10 |
| replication_broadcast | epidemiology | 2 | 1 |
| network_load_diffusion | physics | 6 | 0 |
| starvation_free_scheduling | economics | 1 | 1 |
| adaptive_routing | entomology | 4 | 2 |
| anomaly_detection_no_labels | immunology | 1 | 0 |
| producer_consumer_oscillation | ecology | 1 | 1 |
| admission_control_congestion_collapse | transportation engineering | 1 | 0 |
| stale_value_consensus | social choice theory | 1 | 0 |

(0 = top of a 40-card ranked list.) Mean rank across the 12 problems: **3.00 for text similarity vs. 1.42 for capability match**; median: **1.5 vs. 0.5**. In 9 of 12 cases capability projection moved the donor up (often to rank 0); in 2 cases it was already at parity; in 1 case (`server_bin_packing`) it moved down — discussed below, since it's the one real miss and worth understanding rather than hiding.

## Efficiency and success rate are not the same claim: the budget-sensitivity check

Because the knowledge base has only 40 cards, a large enough attempt budget lets even a poorly-ranking retriever eventually stumble onto the right card by brute force — that's a property of the benchmark's small size, not evidence about representation quality. So the budget was swept from 1 to 40 for both `rag_convergence` and `lcd_convergence` (`results/sensitivity_sweep.json`, `results/chart_budget_sensitivity.png`):

| budget | RAG+convergence LDR | RAG mean attempts | LCD LDR | LCD mean attempts |
|---|---|---|---|---|
| 1 | 0% | 1.00 | 50% | 1.00 |
| 2 | 50% | 2.00 | 75% | 1.50 |
| 3 | 67% | 2.50 | 92% | 1.79 |
| 5 | 75% | 3.21 | 92% | 2.07 |
| 8 | 92% | 4.00 | 92% | 2.50 |
| 10 | 100% | 4.29 | 92% | 2.79 |
| 15 | 100% | 4.64 | 100% | 3.21 |
| 40 | 100% | 6.43 | 100% | 5.00 |

Both conditions reach 100% given enough attempts (as expected for a 40-card knowledge base), and LCD's LDR is at or above RAG's at every single budget tested. But the more informative reading is the right two columns at any fixed row: LCD's mean-attempts curve stays consistently below RAG's, roughly by a factor of 1.3-1.5x throughout. The honest claim this prototype supports is about efficiency and about success rate under a realistic, non-exhaustive budget — not that ordinary RAG is fundamentally incapable of ever finding these mechanisms. A knowledge base with thousands of cards instead of 40 would make the "brute-force eventually finds it" regime much less accessible in practice, which is exactly the regime this benchmark's small size can't speak to (see Limitations).

An earlier draft of `Orchestrator.run()`'s convergence loop included a "stop once the critic's score stops improving" early exit meant to operationalize the spec's `delta_n < epsilon` stopping rule. It triggered on runs of *inapplicable* cards (which all score exactly 0.0 and look like "converged" when really the pipeline just hadn't tried anything relevant yet), which silently capped `rag_convergence` at 66.7% regardless of budget and made the RAG/LCD gap look larger and more budget-insensitive than it really is. This is noted here, not swept under the rug, because it's a good illustration of how easy it is for a convergence heuristic to quietly bias a retrieval comparison; the fix (drop the early exit, use a plain fixed-budget walk down the ranked list) is in `lcd/pipeline.py` and is what produced every number in this document.

## The one miss: `server_bin_packing`

The donor mechanism (simulated annealing) ranks 10th out of 40 in capability space — worse than its rank-7 showing under plain text similarity — so it falls outside a 5-attempt budget for both conditions' worse-off runs, and specifically outside LCD's. Diagnosis (reproducible: `python3 experiments/diagnose_server_bin_packing.py`): the problem statement's language is diffuse enough that no glossary phrase matches it strongly (its top axis scores only 0.032, far below other problems), and in that low-signal regime, two unrelated cards edge out the true donor (similarity 0.2495) purely on incidental shared vocabulary in the 45-phrase projection — an admission-control distractor card (`se_admit_all_retry`, similarity 0.3967; both texts happen to mention "server" and "load") and a visual-composition noise card (`art_rule_of_thirds`, similarity 0.3996; incidental overlap on "balance"/generic phrasing). Eight other cards also edge it out, all crowded into the narrow 0.25-0.40 band the script prints. This is a genuine limitation of TF-IDF as the underlying representation: projecting through a curated glossary reduces lexical-overlap false positives but does not eliminate them, because the projection itself is still computed via lexical cosine similarity, not semantic understanding. A real embedding model or an LLM-based capability extractor would plausibly not make this mistake. This card's wording was deliberately left as originally authored rather than tuned after seeing this result — see README's Design choices for why.

## Control problems

`naive_sufficient_lookup` (binary search suffices; no cross-domain reach needed) passed under every condition except `rag_top1`, where the single-shot text retriever's top candidate is the same-domain `se_linear_scan` distractor (it shares more surface vocabulary — "lookup", "membership check" — with the problem statement than "binary search" does) rather than the correct-and-equally-same-domain `cs_binary_search`. This is a genuinely interesting negative result about single-shot RAG's fragility even with zero cross-domain complexity involved, not a bug: full RAG-with-convergence, both LCD conditions, and the no-retrieval baseline all pass it. It shows the benchmark isn't rigged to make ordinary RAG look bad specifically on cross-domain cases — RAG's single-shot fragility shows up even here.

`impossible_sort_probe` (no card in the knowledge base can satisfy an information-theoretically impossible comparison budget) was correctly rejected — i.e., no condition produced a false positive — across all five conditions, including both convergence-loop conditions trying up to 5 candidates each. This is the safety property the spec asks for explicitly: the system should report "no solution found" rather than force a false match, and every condition did.

## Reading the falsification criteria (spec section 12)

The spec is explicit that "ordinary RAG performing just as well" or "explicit decomposition actively hurting performance" would be legitimate, informative negative results. Neither happened here, but the results are also not a uniform sweep, which is what makes them worth believing:

Explicit decomposition alone, without the convergence loop, underperforms RAG-with-convergence (50% vs. 75% at budget 5) — the capability representation only pulls ahead once paired with retrying down the ranked list, meaning the win in this prototype is a joint property of the representation and the search procedure around it, not the representation in isolation. And one core problem genuinely fails for the full pipeline, for a diagnosed and reported reason. A more adversarial follow-up benchmark, deliberately targeting the lexical-overlap failure mode found here, would be a reasonable next step before trusting this result at any larger scale.

## Limitations and threats to validity

**Scale.** 40 cards and 14 problems is enough to demonstrate the mechanism and get a real, falsifiable, non-hand-waved answer, but not enough to rule out that the result is somewhat particular to a knowledge base this size and this composition. The budget-sensitivity finding above (both conditions hit 100% eventually) is a direct symptom of the knowledge base's small size.

**One author, one pass.** The capability glossary, the 40 cards, and the 14 problems were all authored by the same process in one continuous session. Genuine inter-rater or inter-session reliability (would a different author's glossary produce the same result?) is untested.

**TF-IDF, not semantic embeddings.** Both retrievers share the same lexical representation; the `server_bin_packing` miss is a direct consequence. A version of this experiment using a real sentence-embedding model or an LLM to compute capability similarity would be a meaningfully different (and probably stronger) test, and is the most obvious next step.

**No true historical benchmark.** As discussed in the README, the corpus-cutoff historical-reconstruction design from spec section 8 was not attempted; the `historical_note` fields are context, not a validated experiment.

**Some of the 12 "cross-domain" donors are less foreign to software engineers than the framing implies.** An independent review pass (see README's note on this) flagged that majority quorum voting, SCAN/elevator scheduling, and admission-control/aging-style scheduling all have close, independently well-established analogs already inside standard CS/distributed-systems curricula (quorum reads/writes in Paxos and Raft, disk-arm scheduling in any OS course, aging and congestion control as core scheduling/networking topics) — a well-read software engineer might reach the "SE-native" version of these fixes without needing anything from social choice theory, transportation engineering, or economics specifically, even though this prototype's KB cards are genuinely filed under and worded in those fields. PID control, reservoir sampling, ant colony routing, negative selection, epidemic gossip, heat diffusion, and predator-prey damping are more clearly foreign to typical SWE training. This doesn't change the measured retrieval-ranking result (the retrieval comparison only depends on the cards' actual text, not on how novel their content would strike a reader), but it does mean the "required reaching outside the field" framing is stronger for roughly half the benchmark than the other half, and a stricter version of this benchmark would filter for donor mechanisms with no well-known same-field analog at all.

**The Reconstructor doesn't synthesize code.** Every mechanism's applicability to every problem it's wired to was decided by this prototype's author at authoring time (`CARD_ADAPTERS` in each problem module), not discovered by the system. What the system actually discovers and gets credit for here is *which* wired-up mechanism solves the problem, via retrieval rank — a real but narrower claim than "the system writes the adapter code itself," which would need an LLM in that role (see README).
