"""
The Reasoner interface: this is the pluggable "reasoning engine" the spec
insists is not itself the architecture ("The LLM isn't the architecture. The
LLM is the reasoning engine inside the architecture.")

HeuristicReasoner is the default: deterministic, free, fast, and template
based. It stands in for an LLM at exactly two points -- decompose() and
abstract() -- both of which, in this prototype, are used only to produce a
human-readable trace of *why* the pipeline did what it did. They do not
influence which card gets selected (that is governed entirely by the
retriever's vector-space similarity, computed in lcd/vectorspace.py) or
whether a candidate passes (governed entirely by the objective Critic running
real code against real tests). This separation is deliberate: it keeps the
one experimental variable under test -- retrieval representation -- isolated
from LLM reasoning quality. See README "Design choices" for the tradeoffs.

AnthropicReasoner is an optional real-LLM-backed implementation of the same
interface, provided to show the drop-in path to a genuine reasoning engine.
It activates only if the `anthropic` package is installed and an API key is
configured in the environment; it is not used in the main benchmark run.
Per Improving IT policy, if enabled, it defaults to an approved model
(Claude Sonnet or Haiku).
"""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from typing import List, Tuple

from .schema import KnowledgeCard
from .vectorspace import VectorSpace


class Reasoner(ABC):
    @abstractmethod
    def decompose(self, problem_statement: str) -> List[Tuple[str, float]]:
        """Return the top capability axes this problem projects onto, for the trace."""

    @abstractmethod
    def abstract(self, card: KnowledgeCard) -> str:
        """Return a domain-neutral rendering of the card's mechanism (jargon stripped)."""

    @abstractmethod
    def explain_transfer(self, problem_statement: str, card: KnowledgeCard) -> str:
        """One-paragraph, human-readable rationale for attempting this transfer."""


class HeuristicReasoner(Reasoner):
    def __init__(self, vector_space: VectorSpace):
        self.vs = vector_space

    def decompose(self, problem_statement: str) -> List[Tuple[str, float]]:
        return self.vs.top_glossary_axes(problem_statement, k=6)

    def abstract(self, card: KnowledgeCard) -> str:
        text = card.mechanism_template
        for term in sorted(card.domain_terms, key=len, reverse=True):
            text = re.sub(re.escape(term), "[domain-specific term removed]", text, flags=re.IGNORECASE)
        return text

    def explain_transfer(self, problem_statement: str, card: KnowledgeCard) -> str:
        axes = self.decompose(problem_statement)
        axis_str = "; ".join(a for a, _ in axes[:3])
        return (
            f"Problem projects most strongly onto: {axis_str}. "
            f"Candidate mechanism (abstracted from '{card.title}', domain={card.domain}): "
            f"{self.abstract(card)}"
        )


def _anthropic_available() -> bool:
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic  # noqa: F401
            return True
        except ImportError:
            return False
    return False


class AnthropicReasoner(Reasoner):
    """Optional real-LLM reasoner. Not used by the main benchmark run (see README).
    Defaults to an Improving-IT-approved model string; never Opus/Fable/Mythos."""

    APPROVED_MODEL = "claude-haiku-4-5-20251001"

    def __init__(self, vector_space: VectorSpace, model: str = None):
        if not _anthropic_available():
            raise RuntimeError(
                "AnthropicReasoner requires the `anthropic` package and ANTHROPIC_API_KEY. "
                "Falling back to HeuristicReasoner is recommended for this prototype."
            )
        import anthropic
        self.client = anthropic.Anthropic()
        self.model = model or self.APPROVED_MODEL
        self.vs = vector_space

    def _ask(self, prompt: str) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text

    def decompose(self, problem_statement: str) -> List[Tuple[str, float]]:
        # Real reasoner still reports the same glossary-axis trace for comparability.
        return self.vs.top_glossary_axes(problem_statement, k=6)

    def abstract(self, card: KnowledgeCard) -> str:
        prompt = (
            f"Rewrite the following technique description in fully domain-neutral terms, "
            f"removing every field-specific noun, so the underlying mechanism is visible on "
            f"its own:\n\n{card.text}"
        )
        return self._ask(prompt)

    def explain_transfer(self, problem_statement: str, card: KnowledgeCard) -> str:
        prompt = (
            f"Problem:\n{problem_statement}\n\n"
            f"Candidate mechanism (from {card.domain}): {card.mechanism_template}\n\n"
            f"In 2-3 sentences, does this mechanism genuinely transfer to the problem? Why or why not?"
        )
        return self._ask(prompt)


def get_default_reasoner(vector_space: VectorSpace) -> Reasoner:
    return HeuristicReasoner(vector_space)
