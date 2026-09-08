"""
Two retrievers over the same knowledge base, differing only in representation.

rag_retrieve:          "find documents related to my question" -- ranks cards by
                        raw-text cosine similarity to the problem statement.
                        This is what ordinary RAG does. It has no notion of
                        "capability" or "mechanism" at all.

capability_retrieve:    "find mechanisms exhibiting the capabilities required by
                        my problem, regardless of what their documents are about"
                        -- ranks cards by capability-space cosine similarity.
                        Domain-blind by construction: the scoring function never
                        reads card.domain, so a card cannot win or lose points for
                        being in/out of the problem's nominal field.

Both return a ranked list of (card, score) pairs, most similar first.
"""

from __future__ import annotations

from typing import List, Tuple
from .schema import KnowledgeCard, BenchmarkProblem
from .vectorspace import VectorSpace


def rag_retrieve(problem: BenchmarkProblem, cards: List[KnowledgeCard], vs: VectorSpace,
                  k: int = None) -> List[Tuple[KnowledgeCard, float]]:
    scored = [(c, vs.text_similarity(problem.statement, c.rag_text())) for c in cards]
    scored.sort(key=lambda x: -x[1])
    return scored[:k] if k else scored


def capability_retrieve(problem: BenchmarkProblem, cards: List[KnowledgeCard], vs: VectorSpace,
                         k: int = None) -> List[Tuple[KnowledgeCard, float]]:
    # Note: card.domain is never read here. Retrieval is purely a function of
    # capability_text() similarity in the shared glossary-projected space.
    scored = [(c, vs.capability_similarity(problem.statement, c.capability_text())) for c in cards]
    scored.sort(key=lambda x: -x[1])
    return scored[:k] if k else scored


def cross_representation_distance(problem: BenchmarkProblem, card: KnowledgeCard) -> int:
    """A crude but objective 'how far apart in conventional human taxonomy'
    metric (spec section 9): 0 if the card's domain equals the problem's
    nominal domain (software_engineering for every benchmark problem here),
    1 otherwise. With only one non-SE domain per card this collapses to a
    binary same-field / cross-field indicator, which is enough to test the
    claim that LCD's wins disproportionately come from cross-field cards."""
    return 0 if card.domain == "software_engineering" else 1
