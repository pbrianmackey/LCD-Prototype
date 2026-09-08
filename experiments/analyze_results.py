"""
Builds two charts and a findings table from results/summary.json and
results/sensitivity_sweep.json (run run_benchmark.py and sensitivity_sweep.py
first).

Usage: python3 experiments/analyze_results.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CONDITION_LABELS = {
    "baseline_a_naive": "A: same-domain\nnaive (no retrieval)",
    "rag_top1": "B: text RAG\n(top-1)",
    "rag_convergence": "C: text RAG\n+ convergence",
    "lcd_top1": "D: capability retrieval\n(top-1, no convergence)",
    "lcd_convergence": "E: full LCD\n(capability + convergence)",
}
ORDER = ["baseline_a_naive", "rag_top1", "rag_convergence", "lcd_top1", "lcd_convergence"]
COLORS = ["#9aa0a6", "#f4a261", "#e76f51", "#8ecae6", "#2a9d8f"]


def main():
    results_dir = ROOT / "results"
    with open(results_dir / "summary.json") as f:
        summary = json.load(f)
    with open(results_dir / "sensitivity_sweep.json") as f:
        sweep = json.load(f)

    # ---- Chart 1: LDR by condition (bar chart) ----
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    labels = [CONDITION_LABELS[c] for c in ORDER]
    ldrs = [summary[c]["ldr_core"] * 100 for c in ORDER]
    bars = ax.bar(labels, ldrs, color=COLORS)
    for bar, val in zip(bars, ldrs):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 1.5, f"{val:.0f}%", ha="center", fontsize=10)
    ax.set_ylabel("Latent Discovery Rate (core problems, %)")
    ax.set_title("LDR by condition (12 cross-domain-transfer problems, budget=5)")
    ax.set_ylim(0, 105)
    ax.tick_params(axis="x", labelsize=8.5)
    plt.tight_layout()
    fig.savefig(results_dir / "chart_ldr_by_condition.png", dpi=150)
    plt.close(fig)

    # ---- Chart 2: LDR and mean attempts vs budget ----
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    for condition, color in [("rag_convergence", "#e76f51"), ("lcd_convergence", "#2a9d8f")]:
        rows = [r for r in sweep if r["condition"] == condition]
        rows.sort(key=lambda r: r["budget"])
        budgets = [r["budget"] for r in rows]
        ldrs = [r["ldr"] * 100 for r in rows]
        attempts = [r["mean_attempts"] for r in rows]
        label = "text RAG + convergence" if condition == "rag_convergence" else "full LCD"
        ax1.plot(budgets, ldrs, marker="o", label=label, color=color)
        ax2.plot(budgets, attempts, marker="o", label=label, color=color)
    ax1.set_xlabel("convergence attempt budget")
    ax1.set_ylabel("LDR (core problems, %)")
    ax1.set_title("Success rate vs. attempt budget")
    ax1.set_ylim(0, 105)
    ax1.legend()
    ax2.set_xlabel("convergence attempt budget")
    ax2.set_ylabel("mean attempts used per problem")
    ax2.set_title("Efficiency vs. attempt budget")
    ax2.legend()
    plt.tight_layout()
    fig.savefig(results_dir / "chart_budget_sensitivity.png", dpi=150)
    plt.close(fig)

    print(f"Wrote charts to {results_dir}/chart_ldr_by_condition.png and chart_budget_sensitivity.png")


if __name__ == "__main__":
    main()
