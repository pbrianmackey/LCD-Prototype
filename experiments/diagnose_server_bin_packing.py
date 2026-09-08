"""
Reproduces the FINDINGS.md diagnosis of the one core-problem miss for the
full LCD condition: why does the simulated-annealing donor card rank 10th
(worse than its rank-7 showing under plain text similarity) in capability
space for `server_bin_packing`?

Usage: python3 experiments/diagnose_server_bin_packing.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lcd.schema import load_cards, load_problems
from lcd.vectorspace import build_vector_space

PROBLEM_ID = "server_bin_packing"
DONOR_ID = "statistical_physics_simulated_annealing"


def main():
    cards = load_cards(ROOT / "data" / "knowledge_base.jsonl")
    problems = load_problems(ROOT / "benchmark" / "benchmark.jsonl")
    vs = build_vector_space(cards, problems)
    cards_by_id = {c.id: c for c in cards}

    problem = next(p for p in problems if p.id == PROBLEM_ID)
    donor = cards_by_id[DONOR_ID]

    print(f"Problem statement:\n  {problem.statement}\n")

    print("Problem's top glossary axes (note how low the top score is -- diffuse signal):")
    for phrase, score in vs.top_glossary_axes(problem.statement, k=8):
        print(f"  {score:.3f}  {phrase}")

    print(f"\nDonor ({DONOR_ID}) capability_text:\n  {donor.capability_text()}\n")
    print("Donor's top glossary axes:")
    for phrase, score in vs.top_glossary_axes(donor.capability_text(), k=5):
        print(f"  {score:.3f}  {phrase}")

    donor_sim = vs.capability_similarity(problem.statement, donor.capability_text())
    print(f"\ncapability_similarity(problem, donor) = {donor_sim:.4f}")

    print("\nCards that outrank the donor in capability space, and why (shared surface vocabulary,")
    print("not genuine mechanism relevance):")
    scored = [(c, vs.capability_similarity(problem.statement, c.capability_text())) for c in cards]
    scored.sort(key=lambda x: -x[1])
    donor_rank = next(i for i, (c, s) in enumerate(scored) if c.id == DONOR_ID)
    for rank, (c, s) in enumerate(scored[:donor_rank]):
        print(f"  #{rank}  {s:.4f}  {c.id} [{c.domain}]  capability_text: {c.capability_text()[:90]}...")
    print(f"  #{donor_rank}  {donor_sim:.4f}  {DONOR_ID} [{donor.domain}]  <-- true donor")


if __name__ == "__main__":
    main()
