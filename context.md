
## The experimental design

**Knowledge base** (`data/knowledge_base.jsonl`, 40 cards, 28 fields): 12 genuine cross-domain
donor cards (control theory, statistics, epidemiology, physics, economics, entomology,
immunology, ecology, transportation engineering, social choice theory, operations research) +
1 same-domain CS donor (binary search) + 13 same-domain "software engineering" distractor
cards (topically on-point, mechanistically insufficient) + 14 unrelated-field noise cards
(cooking, music, geology, law, etc. — pure retrieval noise, solve nothing).

Each card has two independent text representations: `text`/`title` (natural domain-native
prose — what RAG embeds) and `capability_tags`/`mechanism_template` (domain-neutral abstracted
description — what capability retrieval embeds). Both get projected through the *same* fitted
TF-IDF vectorizer; only the retrieval method differs in which fields it compares
(`lcd/vectorspace.py`, `lcd/retriever.py`).

**Benchmark** (`benchmark/benchmark.jsonl`, 14 problems): 12 core problems, each a real
simulation/computation with a pass/fail test empirically calibrated (not just asserted) so the
same-domain default genuinely fails and the cross-domain donor genuinely passes; problem
statements are written in plain SWE language with the donor field's jargon deliberately absent
(auto-checked via `leakage_check`). Plus 2 controls: `naive_sufficient_lookup` (same-domain
binary search already suffices — tests the method doesn't force unneeded cross-domain reach)
and `impossible_sort_probe` (information-theoretically impossible; nothing in the KB should
pass — tests the system correctly reports failure rather than a false positive).

**5 conditions** (`lcd/pipeline.py` `CONDITIONS`): `baseline_a_naive` (same-domain, no
retrieval), `rag_top1` (text similarity, 1 attempt), `rag_convergence` (text similarity, up to
5 attempts), `lcd_top1` (capability retrieval, 1 attempt — ablation, no convergence),
`lcd_convergence` (capability retrieval + up to 5 attempts — the full system).

## Results (from `results/summary.json`, budget=5, reproducible exactly via `python3 experiments/run_benchmark.py`)

| condition | LDR (12 core problems) | mean attempts | cross-domain share of wins |
|---|---|---|---|
| A. same-domain naive | 0% (0/12) | 1.00 | — |
| B. text RAG, top-1 | 0% (0/12) | 1.00 | — |
| C. text RAG + convergence | 75% (9/12) | 3.21 | 100% |
| D. capability retrieval, top-1 | 50% (6/12) | 1.00 | 100% |
| E. full LCD (capability + convergence) | **92% (11/12)** | **2.07** | 100% |

Both controls pass correctly under every condition except `rag_top1` fails
`naive_sufficient_lookup` (its top-1 pick is a same-domain distractor, `se_linear_scan`, on
surface lexical overlap — a real, interesting single-shot-RAG fragility finding, not a bug).
`impossible_sort_probe` is correctly rejected by every condition, including both
convergence-loop conditions trying 5 candidates each — no false positives anywhere.

**Budget sensitivity** (`experiments/sensitivity_sweep.py`): with only 40 cards, both
`rag_convergence` and `lcd_convergence` eventually reach 100% given enough attempts (15+), so
the finding is about efficiency and small-budget success rate, not RAG being fundamentally
incapable. LCD's mean-attempts curve stays below RAG's at every budget tested (1 through 40).

**The one core miss**: `server_bin_packing` (donor: simulated annealing) fails for
`lcd_convergence` because the donor ranks 10th in capability space (worse than its rank-7
showing under plain text similarity) — diagnosed and reproducible via
`experiments/diagnose_server_bin_packing.py`: the problem statement's glossary projection is
unusually diffuse (top axis score only 0.032), and in that low-signal regime two unrelated
cards edge out the true donor on incidental shared vocabulary. Left un-fixed on purpose (see
"Design discipline" below). This is a genuine TF-IDF/lexical-representation limitation, not
evidence against the hypothesis.

## Important bug found and fixed mid-build

An earlier version of `Orchestrator.run()`'s convergence loop had a "stop once the critic's
score stops improving" early exit, meant to operationalize the spec's `delta_n < epsilon`
stopping rule. It triggered on runs of *inapplicable* cards (all score exactly 0.0, looking
like "converged" when really nothing relevant had been tried yet), silently capping
`rag_convergence` at 66.7% regardless of budget and making the RAG/LCD gap look larger and more
budget-insensitive than it really is. Fixed by dropping the early exit in favor of a plain
fixed-budget walk down the ranked list — this is what produced every number above. Documented
in `FINDINGS.md` as a cautionary note about convergence heuristics quietly biasing a retrieval
comparison.

## Independent verification

A second, fresh agent (no visibility into the build process) was asked to reproduce the
results from scratch and hunt for rigged thresholds, leaked answers, non-domain-blind
retrieval, or incorrect mechanism implementations. Verdict: numbers reproduced exactly,
distractor baselines are fair (not strawmen — several are literally the same mechanism function
called with the tested feature disabled), retrieval confirmed domain-blind by direct code read,
mechanisms confirmed textbook-correct. One real caveat it raised, since folded into
`FINDINGS.md`: roughly half of the 12 "cross-domain" donor mechanisms (quorum voting, SCAN
scheduling, admission-control aging) have close analogs already standard within CS/distributed-
systems curricula, so the "required reaching outside the field" framing is stronger for the
other half (PID, reservoir sampling, ant colony routing, negative selection, epidemic gossip,
heat diffusion, predator-prey damping) than for all twelve uniformly.

## Design discipline worth knowing about

- The capability glossary (45 phrases) was authored once, before any benchmark problem, and
  never edited afterward to chase a result.
- Card wording that produced the one diagnosed miss was deliberately left as originally
  authored rather than tuned after seeing the result — tuning representation after seeing
  outcomes would make the experiment circular.
- Retrieval rank is the ground-truth-free measurement; pass/fail is entirely from real code
  running real tests (no LLM judgment in the loop for correctness).

## Key simplifications vs. the original spec (all disclosed in README.md "Design choices")

1. **Reasoner is heuristic/deterministic by default**, not an LLM — isolates the
   retrieval-representation variable being tested. `lcd/reasoner.py` has a `Reasoner` ABC;
   `HeuristicReasoner` only populates a human-readable trace, doesn't decide retrieval or
   judge correctness. An optional `AnthropicReasoner` exists (inactive unless
   `ANTHROPIC_API_KEY` set; defaults to an approved Claude model string) but is not used in the
   reported experiment.
2. **Reconstructor selects + invokes pre-written generic mechanism code; it does not
   synthesize code from the abstracted description.** Each problem's `CARD_ADAPTERS` dict
   wires specific (problem, card) pairs to a factory function. A retrieved card with no wired
   adapter is treated as "not applicable" (a real, tested code path — this is exactly what
   makes `impossible_sort_probe` correctly fail everywhere).
3. **Retrieval is TF-IDF, not neural embeddings or an LLM** — deliberately minimal,
   dependency-light, and the direct cause of the one diagnosed miss.
4. **No true historical corpus-cutoff benchmark** (spec's section on discoveries dated before
   a knowledge cutoff) — no reliable dated corpus was available; the 14 synthetic problems are
   the primary benchmark, with `historical_note` fields noting where a problem mirrors a
   documented real transfer (gossip protocols from epidemiology, ACO from entomology, etc.) as
   context, not a validated historical experiment.
5. **Scale**: 40 cards, 14 problems — chosen deliberately small per "prioritize a small
   end-to-end experiment over a large theoretical one."

## How to reproduce / extend

```bash
pip install -r requirements.txt
python3 data/build_knowledge_base.py      # data/knowledge_base.jsonl
python3 benchmark/build_benchmark.py       # benchmark/benchmark.jsonl
python3 experiments/run_benchmark.py       # results/{raw_results,summary}.json
python3 experiments/sensitivity_sweep.py   # results/sensitivity_sweep.json
python3 experiments/analyze_results.py     # results/chart_*.png
python3 -m pytest tests/ -q                # should be 36 passed
python3 demo.py autoscaler_oscillation     # narrated single-problem trace
```

Natural next steps (also in README "Extending this"): swap in `AnthropicReasoner` once
code-synthesis in the Reconstructor is worth tackling; replace TF-IDF with a real embedding
model to test whether the `server_bin_packing` miss is TF-IDF-specific; grow the KB/benchmark
past 40/14; attempt a real dated historical benchmark if a suitable corpus becomes available;
replace the hand-authored glossary with one learned from clustering card texts (the spec's own
stated long-run goal); tighten the benchmark to donor mechanisms with no well-known same-field
CS analog, per the independent review's caveat.

## Where to look for what

- Want the elevator pitch + how to run it → `README.md`
- Want the actual numbers, tables, and honest limitations → `FINDINGS.md`
- Want to see the pipeline reasoning end-to-end on one example → `demo.py`
- Want to see how a specific mechanism works → `lcd/mechanisms/<name>.py` (each has a docstring
  naming its donor field)
- Want to see how a specific problem's test was calibrated → `benchmark/problems/<id>.py`
  (each has a `if __name__ == "__main__"` block printing PASS/FAIL for donor and distractor)
- Want raw per-attempt data → `results/raw_results.json`