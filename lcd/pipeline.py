"""
The six-stage pipeline from the spec, wired up to concrete, testable code.

    PROBLEM
       |
       v
  1. DECOMPOSER            -> Reasoner.decompose(): top capability-glossary axes (trace only)
       |
       v
  2. CAPABILITY SEARCH      -> retriever.rag_retrieve() / retriever.capability_retrieve()
       |
       v
  3. ABSTRACTOR             -> Reasoner.abstract(): strips card.domain_terms (trace + Reconstructor input)
       |
       v
  4. RECONSTRUCTOR          -> Reconstructor.build(): selects+invokes the card's code_skeleton,
       |                        adapted to the problem's interface (see problem harness CARD_ADAPTERS)
       v
  5. CRITIC / VALIDATOR     -> Critic.judge(): runs the harness's real tests. Objective pass/fail.
       |
   reject <-----+-----> candidate
       |               |
       v               v
  update ranking   record success
       |               |
       +-------+-------+
               v
  6. CONVERGENCE AGENT      -> Orchestrator.run(): walks the ranked candidate list until a pass,
                                a fixed attempt budget is exhausted, or (for *_convergence
                                conditions) score stops improving between successive attempts.

Everything after stage 2 is identical regardless of which retriever produced the
ranking -- the ONLY thing that differs between the RAG baseline and LCD is which
list of (card, score) pairs stage 2 hands to stage 4 onward. That is what makes
this a controlled experiment about representation rather than five unrelated
pipelines.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

from .schema import KnowledgeCard, BenchmarkProblem
from .vectorspace import VectorSpace
from .retriever import rag_retrieve, capability_retrieve
from .reasoner import Reasoner

CONDITIONS = ("baseline_a_naive", "rag_top1", "rag_convergence", "lcd_top1", "lcd_convergence")


@dataclass
class AttemptRecord:
    rank: int
    card_id: str
    card_domain: str
    retrieval_score: float
    applicable: bool
    passed: bool
    score: float
    detail: str
    cross_domain: bool
    transfer_rationale: str = ""


@dataclass
class RunResult:
    problem_id: str
    condition: str
    passed: bool = False
    attempts: List[AttemptRecord] = field(default_factory=list)
    winning_card_id: Optional[str] = None
    winning_card_domain: Optional[str] = None
    winning_cross_domain: Optional[bool] = None

    @property
    def num_attempts(self) -> int:
        return len(self.attempts)


def load_harness(module_path: str):
    return importlib.import_module(module_path)


class Reconstructor:
    """Stage 4. See module docstring for what this simplifies away."""

    def build(self, harness, card: KnowledgeCard) -> Tuple[Any, bool]:
        factory = getattr(harness, "CARD_ADAPTERS", {}).get(card.id)
        if factory is None:
            return None, False
        return factory(), True


class Critic:
    """Stage 5. Objective: runs harness.evaluate(candidate) -> (passed, score, detail)."""

    def judge(self, harness, candidate) -> Tuple[bool, float, str]:
        if candidate is None:
            return False, 0.0, "not_applicable: no transfer path implemented for this mechanism"
        try:
            return harness.evaluate(candidate)
        except Exception as e:  # a candidate that raises is just a fail, not a crash of the experiment
            return False, 0.0, f"candidate raised {type(e).__name__}: {e}"


class Orchestrator:
    """Stages 1-2-6 (decompose happens inside explain_transfer for the trace;
    stage 2 dispatches to the right retriever; this class runs the
    convergence loop over stages 3-4-5)."""

    def __init__(self, vector_space: VectorSpace, reasoner: Reasoner):
        self.vs = vector_space
        self.reasoner = reasoner
        self.reconstructor = Reconstructor()
        self.critic = Critic()

    def run(self, problem: BenchmarkProblem, cards: List[KnowledgeCard], condition: str,
            convergence_budget: int = 5) -> RunResult:
        if condition not in CONDITIONS:
            raise ValueError(f"unknown condition '{condition}', expected one of {CONDITIONS}")

        harness = load_harness(problem.harness_module)
        result = RunResult(problem_id=problem.id, condition=condition)

        if condition == "baseline_a_naive":
            card = next(c for c in cards if c.id == problem.baseline_a_card_id)
            ranked = [(card, 1.0)]
        elif condition in ("rag_top1", "rag_convergence"):
            ranked = rag_retrieve(problem, cards, self.vs)
        else:  # lcd_top1, lcd_convergence
            ranked = capability_retrieve(problem, cards, self.vs)

        budget = 1 if condition in ("baseline_a_naive", "rag_top1", "lcd_top1") else convergence_budget

        # Convergence loop: walk the ranked list, trying each candidate in turn,
        # until one passes or the fixed attempt budget is exhausted. Earlier
        # drafts also added a "stop once the critic's score stops improving"
        # early exit, meant to model the spec's Delta_n < epsilon stopping rule.
        # In practice that rule triggered on strings of *inapplicable* cards
        # (which all score exactly 0.0, looking like "converged" when really
        # it's just "nothing tried yet"), cutting the walk short well before
        # the budget was spent and confounding the budget-sensitivity check
        # (see README/FINDINGS). A fixed attempt budget is simpler and
        # doesn't have that failure mode, so that's what this loop does.
        for rank, (card, sim) in enumerate(ranked[:budget]):
            candidate, applicable = self.reconstructor.build(harness, card)
            passed, score, detail = self.critic.judge(harness, candidate)
            cross_domain = card.domain != "software_engineering"
            rationale = self.reasoner.explain_transfer(problem.statement, card)
            result.attempts.append(AttemptRecord(
                rank=rank, card_id=card.id, card_domain=card.domain, retrieval_score=sim,
                applicable=applicable, passed=passed, score=score, detail=detail,
                cross_domain=cross_domain, transfer_rationale=rationale,
            ))
            if passed:
                result.passed = True
                result.winning_card_id = card.id
                result.winning_card_domain = card.domain
                result.winning_cross_domain = cross_domain
                break

        return result
