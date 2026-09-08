#!/usr/bin/env python3
"""
A single narrated run through all six pipeline stages on one example problem,
printing the intermediate representation at each stage. This is meant to be
read, not just executed -- run it and follow along against README.md's
architecture diagram.

Usage: python3 demo.py [problem_id]
Default problem_id: autoscaler_oscillation
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from lcd.schema import load_cards, load_problems
from lcd.vectorspace import build_vector_space
from lcd.retriever import rag_retrieve, capability_retrieve
from lcd.reasoner import get_default_reasoner
from lcd.pipeline import Orchestrator, load_harness


def hr(title):
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def main():
    problem_id = sys.argv[1] if len(sys.argv) > 1 else "autoscaler_oscillation"

    cards = load_cards(ROOT / "data" / "knowledge_base.jsonl")
    problems = load_problems(ROOT / "benchmark" / "benchmark.jsonl")
    problem = next((p for p in problems if p.id == problem_id), None)
    if problem is None:
        print(f"Unknown problem_id '{problem_id}'. Available: {[p.id for p in problems]}")
        sys.exit(1)

    vs = build_vector_space(cards, problems)
    reasoner = get_default_reasoner(vs)

    hr("PROBLEM")
    print(problem.statement)
    print(f"\n(ground truth, not given to the system: donor_card_id={problem.donor_card_id!r}, "
          f"used only for scoring after the fact)")

    hr("1. DECOMPOSER  --  top capability-glossary axes this problem projects onto")
    for phrase, score in reasoner.decompose(problem.statement):
        print(f"  {score:.3f}  {phrase}")

    hr("2. CAPABILITY SEARCH ENGINE  --  top 5 by each retriever")
    rag_ranked = rag_retrieve(problem, cards, vs, k=5)
    cap_ranked = capability_retrieve(problem, cards, vs, k=5)
    print("ordinary RAG (raw text similarity):")
    for rank, (card, score) in enumerate(rag_ranked):
        flag = "  <-- true donor" if card.id == problem.donor_card_id else ""
        print(f"  #{rank}  {score:.3f}  {card.id} [{card.domain}]{flag}")
    print("\ncapability retrieval (projected through the 45-phrase glossary, domain-blind):")
    for rank, (card, score) in enumerate(cap_ranked):
        flag = "  <-- true donor" if card.id == problem.donor_card_id else ""
        print(f"  #{rank}  {score:.3f}  {card.id} [{card.domain}]{flag}")

    hr("4-5-6. RECONSTRUCTOR + CRITIC + CONVERGENCE, walked down the capability-ranked list")
    orchestrator = Orchestrator(vs, reasoner)
    result = orchestrator.run(problem, cards, "lcd_convergence", convergence_budget=5)
    for a in result.attempts:
        outcome = "PASS" if a.passed else ("not applicable" if not a.applicable else "fail")
        print(f"  attempt rank={a.rank} card={a.card_id} [{a.card_domain}] "
              f"cross_domain={a.cross_domain} -> {outcome}: {a.detail}")

    abstracted_card_id = result.winning_card_id or cap_ranked[0][0].id
    abstracted_card = next(c for c in cards if c.id == abstracted_card_id)
    hr(f"3. ABSTRACTOR (shown after the fact)  --  domain-neutral rendering of '{abstracted_card.id}'"
       f"{' (the card that ultimately passed)' if result.winning_card_id else ' (top capability-ranked card)'}")
    print(f"original (domain-native) text:\n  {abstracted_card.text}")
    print(f"\nabstracted (jargon stripped):\n  {reasoner.abstract(abstracted_card)}")

    hr("RESULT")
    if result.passed:
        print(f"PASSED using '{result.winning_card_id}' ({result.winning_card_domain}), "
              f"cross_domain={result.winning_cross_domain}, after {result.num_attempts} attempt(s).")
    else:
        print(f"FAILED after {result.num_attempts} attempt(s) -- no candidate in the ranked list passed.")


if __name__ == "__main__":
    main()
