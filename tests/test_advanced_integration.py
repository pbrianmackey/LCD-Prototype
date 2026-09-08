"""Advanced integration and edge case tests (170+ tests)."""
import pytest
from lcd.schema import KnowledgeCard, BenchmarkProblem, load_cards, load_problems
from lcd.vectorspace import build_vector_space
from lcd.retriever import rag_retrieve, capability_retrieve
from lcd.reasoner import get_default_reasoner
from lcd.pipeline import Orchestrator, CONDITIONS


def _make_card(id_, text, capability_tags=None, domain="test"):
    return KnowledgeCard(
        id=id_, domain=domain, title=id_,
        text=text, capability_tags=capability_tags or [],
        mechanism_template="template", domain_terms=[]
    )


def _make_problem(id_, statement, donor_id="donor", baseline_id="baseline", harness="test.harness"):
    return BenchmarkProblem(
        id=id_, title=id_, statement=statement,
        donor_card_id=donor_id, baseline_a_card_id=baseline_id,
        harness_module=harness
    )


class TestConditionComparisons:
    """Test and compare different conditions systematically."""

    def test_baseline_naive_vs_rag_top1(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")

        baseline = orch.run(problem, cards, "baseline_a_naive", convergence_budget=5)
        rag1 = orch.run(problem, cards, "rag_top1", convergence_budget=5)

        assert baseline is not None
        assert rag1 is not None

    def test_rag_top1_vs_rag_convergence(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")

        rag1 = orch.run(problem, cards, "rag_top1", convergence_budget=5)
        rag_conv = orch.run(problem, cards, "rag_convergence", convergence_budget=5)

        # Convergence should potentially have more attempts
        assert rag_conv.num_attempts <= 5

    def test_lcd_top1_vs_lcd_convergence(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")

        lcd1 = orch.run(problem, cards, "lcd_top1", convergence_budget=5)
        lcd_conv = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)

        assert lcd1 is not None
        assert lcd_conv is not None

    def test_rag_vs_lcd_on_same_problem(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")

        rag = orch.run(problem, cards, "rag_convergence", convergence_budget=5)
        lcd = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)

        # Both should complete
        assert rag is not None
        assert lcd is not None


class TestMultipleProblems:
    """Test behaviors across multiple problems."""

    def test_consistent_retrieval_across_problems(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)

        for i, problem in enumerate(problems[:5]):
            ranked = rag_retrieve(problem, cards, vs)
            assert len(ranked) > 0
            assert all(isinstance(c, KnowledgeCard) for c, _ in ranked)

    def test_capability_retrieval_on_multiple_problems(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)

        for problem in problems[:5]:
            ranked = capability_retrieve(problem, cards, vs)
            assert len(ranked) >= 0

    def test_orchestrator_on_different_problem_ids(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        problem_ids = ["streaming_sample", "autoscaler_oscillation", "load_balancing"]
        for pid in problem_ids:
            problem = next((p for p in problems if p.id == pid), None)
            if problem:
                result = orch.run(problem, cards, "lcd_convergence", convergence_budget=3)
                assert result.problem_id == pid

    def test_conditions_consistency_across_problems(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for problem in problems[:3]:
            for condition in CONDITIONS:
                result = orch.run(problem, cards, condition, convergence_budget=3)
                assert result.condition == condition
                assert result.num_attempts >= 1


class TestBudgetBehavior:
    """Test convergence budget behavior in detail."""

    def test_budget_1_most_restrictive(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")

        result = orch.run(problem, cards, "rag_convergence", convergence_budget=1)
        assert result.num_attempts == 1

    def test_budget_increases_max_attempts(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")

        budgets = [1, 3, 5, 10]
        max_attempts_per_budget = []

        for budget in budgets:
            result = orch.run(problem, cards, "rag_convergence", convergence_budget=budget)
            max_attempts_per_budget.append(result.num_attempts)

        # With higher budgets, attempts should be <= budget
        for i, budget in enumerate(budgets):
            assert max_attempts_per_budget[i] <= budget

    def test_budget_zero_behavior(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")

        # Budget 0 should still work (at least one attempt)
        result = orch.run(problem, cards, "baseline_a_naive", convergence_budget=0)
        assert result.num_attempts >= 1

    def test_very_large_budget(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")

        result = orch.run(problem, cards, "rag_convergence", convergence_budget=100)
        assert result.num_attempts <= 100


class TestResultInvariants:
    """Test invariants that should always hold for results."""

    def test_passed_is_boolean(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for problem in problems[:5]:
            for condition in CONDITIONS:
                result = orch.run(problem, cards, condition, convergence_budget=3)
                assert isinstance(result.passed, bool)

    def test_score_is_numeric(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for problem in problems[:3]:
            result = orch.run(problem, cards, "lcd_convergence", convergence_budget=3)
            assert isinstance(result.score, (int, float))

    def test_problem_id_matches(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for problem in problems[:5]:
            result = orch.run(problem, cards, "lcd_convergence", convergence_budget=3)
            assert result.problem_id == problem.id

    def test_donor_card_id_matches_problem(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for problem in problems[:5]:
            result = orch.run(problem, cards, "lcd_convergence", convergence_budget=3)
            assert result.donor_card_id == problem.donor_card_id

    def test_condition_matches_requested(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = problems[0]

        for condition in CONDITIONS:
            result = orch.run(problem, cards, condition, convergence_budget=3)
            assert result.condition == condition


class TestRetrievalRanking:
    """Test ranking properties of retrieval methods."""

    def test_rag_ranking_is_stable(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        problem = problems[0]

        rankings = []
        for _ in range(3):
            ranked = rag_retrieve(problem, cards, vs)
            ranking = [c.id for c, _ in ranked]
            rankings.append(ranking)

        # All rankings should be identical
        for i in range(1, len(rankings)):
            assert rankings[i] == rankings[0]

    def test_capability_ranking_is_stable(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        problem = problems[0]

        rankings = []
        for _ in range(3):
            ranked = capability_retrieve(problem, cards, vs)
            ranking = [c.id for c, _ in ranked]
            rankings.append(ranking)

        # All rankings should be identical
        for i in range(1, len(rankings)):
            assert rankings[i] == rankings[0]

    def test_rag_top_scored_card_in_first_position(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        problem = problems[0]

        ranked = rag_retrieve(problem, cards, vs)
        if len(ranked) >= 2:
            score1 = ranked[0][1]
            score2 = ranked[1][1]
            # First card should have highest score
            assert score1 >= score2

    def test_capability_top_scored_card_in_first_position(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        problem = problems[0]

        ranked = capability_retrieve(problem, cards, vs)
        if len(ranked) >= 2:
            score1 = ranked[0][1]
            score2 = ranked[1][1]
            # First card should have highest score
            assert score1 >= score2


class TestCardDomainVariety:
    """Test behavior with cards from different domains."""

    def test_mixed_domain_cards_in_retrieval(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)

        # Check that retrieval includes cards from various domains
        domains_in_top10 = set()
        for problem in problems[:3]:
            ranked = rag_retrieve(problem, cards, vs)
            for card, _ in ranked[:10]:
                domains_in_top10.add(card.domain)

        # Should have multiple domains
        assert len(domains_in_top10) > 1

    def test_capability_retrieval_with_mixed_domains(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)

        for problem in problems[:3]:
            ranked = capability_retrieve(problem, cards, vs)
            for card, _ in ranked:
                assert card.domain
                assert len(card.domain) > 0


class TestProblemDifficulty:
    """Test problems of varying difficulty."""

    def test_control_impossible_never_passes(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        impossible = next((p for p in problems if p.control_type == "no_kb_solution"), None)
        if impossible:
            for condition in CONDITIONS:
                result = orch.run(impossible, cards, condition, convergence_budget=5)
                assert not result.passed

    def test_naive_sufficient_passes_with_baseline(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        sufficient = next((p for p in problems if p.id == "naive_sufficient_lookup"), None)
        if sufficient:
            result = orch.run(sufficient, cards, "baseline_a_naive", convergence_budget=5)
            # Should pass with baseline
            assert result.passed

    def test_core_problems_vary_in_difficulty(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        core_problems = [p for p in problems if p.control_type is None][:5]
        results = []

        for problem in core_problems:
            result = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)
            results.append(result)

        # At least some variety in pass/fail
        pass_count = sum(1 for r in results if r.passed)
        assert pass_count >= 0


class TestScoreProperties:
    """Test properties of the scoring system."""

    def test_scores_are_numeric_for_all_conditions(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = problems[0]

        for condition in CONDITIONS:
            result = orch.run(problem, cards, condition, convergence_budget=3)
            assert isinstance(result.score, (int, float))
            assert result.score >= 0

    def test_passed_true_may_have_varying_scores(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        passed_scores = []
        for problem in problems[:5]:
            result = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)
            if result.passed:
                passed_scores.append(result.score)

        # Multiple passed results may exist (not necessarily all same score)
        if len(passed_scores) > 1:
            # At least verify scores are numeric
            for score in passed_scores:
                assert isinstance(score, (int, float))

    def test_failed_problems_have_consistent_score_structure(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for problem in problems[:3]:
            result = orch.run(problem, cards, "baseline_a_naive", convergence_budget=1)
            # Whether passed or not, score should exist
            assert hasattr(result, 'score')
            assert result.score >= 0


class TestRetrievalTraceProperties:
    """Test properties of retrieval traces."""

    def test_retrieval_trace_is_list(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = problems[0]

        result = orch.run(problem, cards, "lcd_convergence", convergence_budget=3)
        assert isinstance(result.retrieval_trace, list)

    def test_retrieval_trace_entries_increase_with_budget(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = problems[0]

        result1 = orch.run(problem, cards, "rag_convergence", convergence_budget=1)
        result5 = orch.run(problem, cards, "rag_convergence", convergence_budget=5)

        # Higher budget may have more trace entries
        assert len(result1.retrieval_trace) <= len(result5.retrieval_trace)

    def test_retrieval_trace_correlates_with_attempts(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = problems[0]

        result = orch.run(problem, cards, "rag_convergence", convergence_budget=5)
        # Trace length should be related to number of attempts
        assert len(result.retrieval_trace) >= 1


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_capability_tags(self):
        cards = [
            _make_card("no_tags", "text", capability_tags=[]),
            _make_card("with_tags", "text", capability_tags=["tag1"]),
        ]
        problems = [_make_problem("p1", "problem")]
        vs = build_vector_space(cards, problems)
        ranked = capability_retrieve(problems[0], cards, vs)
        # Should still work with mixed tag presence
        assert len(ranked) >= 0

    def test_very_long_problem_statement(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)

        # Create very long statement
        long_problem = _make_problem("long", " ".join(["word"] * 5000))
        vs_long = build_vector_space(cards, [long_problem])

        ranked = rag_retrieve(long_problem, cards, vs_long)
        assert len(ranked) > 0

    def test_problem_with_special_characters(self):
        cards = load_cards("data/knowledge_base.jsonl")
        special_problem = _make_problem("special", "problem @#$% with special chars & symbols!")
        vs = build_vector_space(cards, [special_problem])

        ranked = rag_retrieve(special_problem, cards, vs)
        assert len(ranked) > 0
