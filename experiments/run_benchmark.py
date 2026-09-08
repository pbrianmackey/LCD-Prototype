"""
Runs all 5 conditions across all 14 benchmark problems and saves raw results.

Conditions:
  baseline_a_naive   -- same-domain default, no retrieval at all
  rag_top1           -- ordinary text-similarity RAG, single attempt
  rag_convergence    -- ordinary text-similarity RAG, up to 5 attempts down the ranked list
  lcd_top1           -- capability-vector retrieval, single attempt (ablation: no convergence)
  lcd_convergence    -- full Latent Capability Discovery: capability retrieval + convergence loop

Usage: python3 experiments/run_benchmark.py
"""
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lcd.schema import load_cards, load_problems
from lcd.vectorspace import build_vector_space
from lcd.reasoner import get_default_reasoner
from lcd.pipeline import Orchestrator, CONDITIONS
from lcd.metrics import summarize, leakage_check

CONVERGENCE_BUDGET = 5


def main():
    cards = load_cards(ROOT / "data" / "knowledge_base.jsonl")
    problems = load_problems(ROOT / "benchmark" / "benchmark.jsonl")
    cards_by_id = {c.id: c for c in cards}

    print(f"Loaded {len(cards)} knowledge cards, {len(problems)} benchmark problems.\n")

    print("=== Leakage check (donor jargon must not appear in problem statements) ===")
    any_leak = False
    for p in problems:
        leaked = leakage_check(p, cards_by_id)
        if leaked:
            any_leak = True
            print(f"  LEAK in {p.id}: {leaked}")
    print("  (none found)" if not any_leak else "  ^^ FIX BEFORE TRUSTING RESULTS")
    print()

    vs = build_vector_space(cards, problems)
    reasoner = get_default_reasoner(vs)
    orchestrator = Orchestrator(vs, reasoner)

    all_results = {}  # condition -> [RunResult as dict]
    summaries = {}

    for condition in CONDITIONS:
        run_results = []
        for p in problems:
            r = orchestrator.run(p, cards, condition, convergence_budget=CONVERGENCE_BUDGET)
            run_results.append(r)
        all_results[condition] = run_results
        summaries[condition] = summarize(run_results, problems)

    # ---- print summary table ----
    print("=== Summary (core = 12 cross-domain-transfer problems, excludes the 2 controls) ===")
    header = f"{'condition':20s} {'LDR (core)':11s} {'core pass':10s} {'x-domain win %':15s} {'mean attempts':14s}"
    print(header)
    print("-" * len(header))
    for condition in CONDITIONS:
        s = summaries[condition]
        print(f"{condition:20s} {s.ldr:<11.2%} {s.n_core_passed}/{s.n_core:<8d} "
              f"{s.cross_domain_win_fraction:<15.0%} {s.mean_attempts:<14.2f}")

    print("\n=== Control problems ===")
    for condition in CONDITIONS:
        s = summaries[condition]
        print(f"{condition:20s} naive_sufficient_lookup passed={bool(s.n_control_naive_sufficient_passed)}  "
              f"impossible_sort_probe correctly_rejected={bool(s.n_control_no_kb_solution_correctly_rejected)}")

    # ---- per-problem detail ----
    print("\n=== Per-problem pass/fail by condition ===")
    problem_ids = [p.id for p in problems]
    colw = 16
    print(" " * 42 + "".join(f"{c[:14]:16s}" for c in CONDITIONS))
    for pid in problem_ids:
        row = f"{pid:42s}"
        for condition in CONDITIONS:
            r = summaries[condition].per_problem[pid]
            mark = "PASS" if r.passed else "fail"
            winner = f"({r.winning_card_id})" if r.passed else f"(x{r.num_attempts})"
            cell = f"{mark}{winner}"
            row += f"{cell[:15]:16s}"
        print(row)

    # ---- save raw results ----
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    serializable = {}
    for condition, run_results in all_results.items():
        serializable[condition] = [
            {
                "problem_id": r.problem_id,
                "condition": r.condition,
                "passed": r.passed,
                "winning_card_id": r.winning_card_id,
                "winning_card_domain": r.winning_card_domain,
                "winning_cross_domain": r.winning_cross_domain,
                "num_attempts": r.num_attempts,
                "attempts": [asdict(a) for a in r.attempts],
            }
            for r in run_results
        ]
    with open(out_dir / "raw_results.json", "w") as f:
        json.dump(serializable, f, indent=2)
    print(f"\nSaved raw results to {out_dir / 'raw_results.json'}")

    summary_out = {
        condition: {
            "ldr_core": s.ldr,
            "n_core_passed": s.n_core_passed,
            "n_core": s.n_core,
            "cross_domain_win_fraction": s.cross_domain_win_fraction,
            "cross_domain_wins": s.cross_domain_wins,
            "same_domain_wins": s.same_domain_wins,
            "mean_attempts": s.mean_attempts,
            "control_naive_sufficient_passed": bool(s.n_control_naive_sufficient_passed),
            "control_no_kb_solution_correctly_rejected": bool(s.n_control_no_kb_solution_correctly_rejected),
        }
        for condition, s in summaries.items()
    }
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary_out, f, indent=2)
    print(f"Saved summary to {out_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
