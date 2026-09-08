"""
Metrics from spec section 9, operationalized against what this prototype can
actually measure.

  Latent Discovery Rate (LDR): passed / attempted, computed separately for the
    12 core cross-domain-transfer problems (the real test) and reported
    alongside (not blended with) the 2 control problems.

  Novelty: whether the exact winning mechanism name/jargon appears verbatim in
    the problem statement. Checked automatically (leakage_check) -- if a
    donor card's domain-specific terms leak into the statement, a "win" would
    be meaningless (the retriever could match on the leaked word instead of a
    genuine capability match).

  Evidence availability: True for all 12 core problems by construction (the
    donor card is always present in the knowledge base); False only for the
    no_kb_solution control, where no card should pass.

  Cross-representation distance: 0/1 indicator of whether the WINNING card's
    domain differs from the problem's nominal domain (software_engineering
    for every problem here). Reported as the fraction of a condition's wins
    that are cross-domain.

  Validity: pass/fail from the objective Critic (real code vs real tests) --
    already recorded on every AttemptRecord/RunResult; this module just
    aggregates it.

  Efficiency: mean number of attempts (retrieval+critic iterations) consumed
    per problem under each condition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .schema import KnowledgeCard, BenchmarkProblem
from .pipeline import RunResult


def leakage_check(problem: BenchmarkProblem, cards_by_id: Dict[str, KnowledgeCard]) -> List[str]:
    """Returns a list of leaked terms (should be empty for a well-posed problem)."""
    if problem.donor_card_id == "NONE":
        return []
    donor = cards_by_id[problem.donor_card_id]
    statement_lower = problem.statement.lower()
    leaked = [term for term in donor.domain_terms if term.lower() in statement_lower]
    return leaked


@dataclass
class ConditionSummary:
    condition: str
    n_core: int = 0
    n_core_passed: int = 0
    n_control_naive_sufficient_passed: int = 0
    n_control_no_kb_solution_correctly_rejected: int = 0
    cross_domain_wins: int = 0
    same_domain_wins: int = 0
    total_attempts: int = 0
    per_problem: Dict[str, RunResult] = field(default_factory=dict)

    @property
    def ldr(self) -> float:
        return self.n_core_passed / self.n_core if self.n_core else 0.0

    @property
    def mean_attempts(self) -> float:
        n = len(self.per_problem)
        return self.total_attempts / n if n else 0.0

    @property
    def cross_domain_win_fraction(self) -> float:
        total_wins = self.cross_domain_wins + self.same_domain_wins
        return self.cross_domain_wins / total_wins if total_wins else 0.0


def summarize(results: List[RunResult], problems: List[BenchmarkProblem]) -> ConditionSummary:
    problems_by_id = {p.id: p for p in problems}
    assert results, "no results to summarize"
    condition = results[0].condition
    summary = ConditionSummary(condition=condition)
    for r in results:
        problem = problems_by_id[r.problem_id]
        summary.per_problem[r.problem_id] = r
        summary.total_attempts += r.num_attempts
        if problem.control_type == "naive_sufficient":
            if r.passed:
                summary.n_control_naive_sufficient_passed += 1
            continue
        if problem.control_type == "no_kb_solution":
            if not r.passed:
                summary.n_control_no_kb_solution_correctly_rejected += 1
            continue
        # core problem
        summary.n_core += 1
        if r.passed:
            summary.n_core_passed += 1
            if r.winning_cross_domain:
                summary.cross_domain_wins += 1
            else:
                summary.same_domain_wins += 1
    return summary
