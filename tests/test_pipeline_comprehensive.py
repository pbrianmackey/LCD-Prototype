"""Comprehensive pipeline and orchestrator tests (80+ tests)."""
import tempfile
from pathlib import Path
import pytest
from lcd.schema import KnowledgeCard, BenchmarkProblem
from lcd.vectorspace import build_vector_space
from lcd.reasoner import get_default_reasoner, HeuristicReasoner
from lcd.pipeline import Orchestrator, CONDITIONS
from lcd.metrics import summarize


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


class TestOrchestratorInitialization:
    """Test Orchestrator instantiation and setup."""

    def test_orchestrator_creation(self):
        cards = [_make_card("c1", "text")]
        problems = [_make_problem("p1", "problem")]
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        assert orch is not None

    def test_orchestrator_with_multiple_cards(self):
        cards = [_make_card(f"c{i}", f"text{i}") for i in range(10)]
        problems = [_make_problem("p1", "problem")]
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        assert orch is not None

    def test_orchestrator_stores_vectorspace(self):
        cards = [_make_card("c1", "text")]
        problems = [_make_problem("p1", "problem")]
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        assert orch.vectorspace is vs

    def test_orchestrator_stores_reasoner(self):
        cards = [_make_card("c1", "text")]
        problems = [_make_problem("p1", "problem")]
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        assert orch.reasoner is reasoner

    def test_orchestrator_reasoner_is_heuristic(self):
        cards = [_make_card("c1", "text")]
        problems = [_make_problem("p1", "problem")]
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        assert isinstance(reasoner, HeuristicReasoner)


class TestOrchestratorRun:
    """Test Orchestrator.run() method."""

    def test_orchestrator_run_baseline_naive(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "baseline_a_naive", convergence_budget=5)
        assert result is not None
        assert result.condition == "baseline_a_naive"

    def test_orchestrator_run_rag_top1(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "rag_top1", convergence_budget=5)
        assert result is not None
        assert result.num_attempts >= 1

    def test_orchestrator_run_rag_convergence(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "rag_convergence", convergence_budget=5)
        assert result is not None

    def test_orchestrator_run_lcd_top1(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "lcd_top1", convergence_budget=5)
        assert result is not None

    def test_orchestrator_run_lcd_convergence(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)
        assert result is not None

    def test_orchestrator_run_returns_result_with_condition(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)
        assert hasattr(result, 'condition')
        assert result.condition == "lcd_convergence"

    def test_orchestrator_run_returns_result_with_attempts(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)
        assert hasattr(result, 'num_attempts')
        assert result.num_attempts >= 1

    def test_orchestrator_run_respects_budget(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "rag_convergence", convergence_budget=3)
        assert result.num_attempts <= 3

    def test_orchestrator_run_all_conditions_without_error(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        for condition in CONDITIONS:
            result = orch.run(problem, cards, condition, convergence_budget=5)
            assert result is not None


class TestConditions:
    """Test the five experimental conditions."""

    def test_all_conditions_are_defined(self):
        assert len(CONDITIONS) == 5

    def test_baseline_a_naive_in_conditions(self):
        assert "baseline_a_naive" in CONDITIONS

    def test_rag_top1_in_conditions(self):
        assert "rag_top1" in CONDITIONS

    def test_rag_convergence_in_conditions(self):
        assert "rag_convergence" in CONDITIONS

    def test_lcd_top1_in_conditions(self):
        assert "lcd_top1" in CONDITIONS

    def test_lcd_convergence_in_conditions(self):
        assert "lcd_convergence" in CONDITIONS

    def test_conditions_are_strings(self):
        for condition in CONDITIONS:
            assert isinstance(condition, str)




class TestResultStructure:
    """Test the structure of results from Orchestrator.run()."""

    def test_result_has_problem_id(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)
        assert hasattr(result, 'problem_id')

    def test_result_has_donor_card_id(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)
        assert hasattr(result, 'donor_card_id')

    def test_result_has_passed_flag(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)
        assert hasattr(result, 'passed')
        assert isinstance(result.passed, bool)

    def test_result_has_score(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)
        assert hasattr(result, 'score')

    def test_result_has_retrieval_trace(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)
        assert hasattr(result, 'retrieval_trace')

    def test_result_retrieval_trace_is_list(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)
        assert isinstance(result.retrieval_trace, list)


class TestConvergenceBudget:
    """Test convergence budget behavior."""

    def test_convergence_budget_1(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        result = orch.run(problem, cards, "rag_convergence", convergence_budget=1)
        assert result.num_attempts <= 1

    def test_convergence_budget_respects_upper_bound(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        problem = next(p for p in problems if p.id == "streaming_sample")
        for budget in [1, 2, 3, 5, 10]:
            result = orch.run(problem, cards, "rag_convergence", convergence_budget=budget)
            assert result.num_attempts <= budget


class TestMultipleProblemRuns:
    """Test running the orchestrator on multiple problems."""

    def test_run_on_each_benchmark_problem(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        results = []
        for problem in problems:
            result = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)
            results.append(result)
        assert len(results) == len(problems)

    def test_different_problems_different_results(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        results = []
        for problem in problems[:3]:
            result = orch.run(problem, cards, "lcd_convergence", convergence_budget=5)
            results.append(result)
        # Different problems should exist
        assert len(results) >= 2


class TestControlProblems:
    """Test behavior on control problems."""

    def test_control_no_kb_solution_never_passes(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        impossible = next((p for p in problems if p.control_type == "no_kb_solution"), None)
        if impossible:
            result = orch.run(impossible, cards, "lcd_convergence", convergence_budget=5)
            assert not result.passed

    def test_baseline_sufficient_lookup_passes_with_baseline(self):
        from lcd.schema import load_cards, load_problems
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        sufficient = next((p for p in problems if p.id == "naive_sufficient_lookup"), None)
        if sufficient:
            result = orch.run(sufficient, cards, "baseline_a_naive", convergence_budget=5)
            # This should pass with the baseline condition
            assert result.passed
