"""
Sweeps the convergence-attempt budget for rag_convergence and lcd_convergence
to check the headline result (budget=5) isn't an artifact of a
cherry-picked budget. Since the knowledge base has only 40 cards, both
conditions reach 100% LDR eventually if given a large enough budget (an
exhaustive-enough search finds the donor card no matter how it's ranked) --
the interesting, stable finding is that LCD reaches the same or better LDR
using consistently fewer attempts, and that at small/realistic budgets (3-5)
LCD's success-rate advantage is large, not just its efficiency advantage.

Usage: python3 experiments/sensitivity_sweep.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lcd.schema import load_cards, load_problems
from lcd.vectorspace import build_vector_space
from lcd.reasoner import get_default_reasoner
from lcd.pipeline import Orchestrator
from lcd.metrics import summarize

BUDGETS = [1, 2, 3, 4, 5, 8, 10, 15, 20, 40]


def main():
    cards = load_cards(ROOT / "data" / "knowledge_base.jsonl")
    problems = load_problems(ROOT / "benchmark" / "benchmark.jsonl")
    vs = build_vector_space(cards, problems)
    reasoner = get_default_reasoner(vs)
    orch = Orchestrator(vs, reasoner)

    rows = []
    print(f"{'budget':8s} {'condition':18s} {'LDR':8s} {'passed':8s} {'mean_attempts':14s}")
    for budget in BUDGETS:
        for condition in ["rag_convergence", "lcd_convergence"]:
            results = [orch.run(p, cards, condition, convergence_budget=budget) for p in problems]
            s = summarize(results, problems)
            print(f"{budget:<8d} {condition:18s} {s.ldr:<8.2%} {s.n_core_passed}/{s.n_core:<6d} {s.mean_attempts:<14.2f}")
            rows.append({
                "budget": budget, "condition": condition, "ldr": s.ldr,
                "n_core_passed": s.n_core_passed, "n_core": s.n_core,
                "mean_attempts": s.mean_attempts,
            })

    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "sensitivity_sweep.json", "w") as f:
        json.dump(rows, f, indent=2)
    print(f"\nSaved to {out_dir / 'sensitivity_sweep.json'}")


if __name__ == "__main__":
    main()
