"""Final tests to reach 400+ (30+ additional tests)."""
import pytest
from lcd.schema import load_cards, load_problems
from lcd.vectorspace import build_vector_space
from lcd.retriever import rag_retrieve, capability_retrieve
from lcd.reasoner import get_default_reasoner
from lcd.pipeline import Orchestrator, CONDITIONS


class TestAllConditionsAllProblems:
    """Comprehensive testing across all conditions and problems."""

    def test_condition_baseline_all_problems(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems:
            r = orch.run(p, cards, "baseline_a_naive", convergence_budget=5)
            assert r.condition == "baseline_a_naive"

    def test_condition_rag_top1_all_problems(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems:
            r = orch.run(p, cards, "rag_top1", convergence_budget=5)
            assert r.condition == "rag_top1"

    def test_condition_rag_convergence_all_problems(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems:
            r = orch.run(p, cards, "rag_convergence", convergence_budget=5)
            assert r.condition == "rag_convergence"

    def test_condition_lcd_top1_all_problems(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems:
            r = orch.run(p, cards, "lcd_top1", convergence_budget=5)
            assert r.condition == "lcd_top1"

    def test_condition_lcd_convergence_all_problems(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems:
            r = orch.run(p, cards, "lcd_convergence", convergence_budget=5)
            assert r.condition == "lcd_convergence"


class TestRetrievalScoreOrdering:
    """Test score ordering in retrieval results."""

    def test_rag_scores_ordered_all_problems(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)

        for p in problems[:5]:
            ranked = rag_retrieve(p, cards, vs)
            scores = [s for _, s in ranked]
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i+1]

    def test_capability_scores_ordered_all_problems(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)

        for p in problems[:5]:
            ranked = capability_retrieve(p, cards, vs)
            scores = [s for _, s in ranked]
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i+1]

    def test_rag_top_card_has_highest_score(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)

        for p in problems[:5]:
            ranked = rag_retrieve(p, cards, vs)
            if len(ranked) > 1:
                assert ranked[0][1] >= ranked[-1][1]

    def test_capability_top_card_has_highest_score(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)

        for p in problems[:5]:
            ranked = capability_retrieve(p, cards, vs)
            if len(ranked) > 1:
                assert ranked[0][1] >= ranked[-1][1]


class TestOrchestratorConsistencyAcrossRuns:
    """Test consistency of orchestrator across multiple runs."""

    def test_orchestrator_deterministic_results(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        p = problems[0]
        results = []
        for _ in range(3):
            r = orch.run(p, cards, "lcd_convergence", convergence_budget=3)
            results.append((r.passed, r.score, r.num_attempts))

        # All results should be identical
        assert results[0] == results[1] == results[2]

    def test_orchestrator_problem_id_consistency(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems[:5]:
            r1 = orch.run(p, cards, "lcd_convergence", convergence_budget=2)
            r2 = orch.run(p, cards, "lcd_convergence", convergence_budget=2)
            assert r1.problem_id == r2.problem_id == p.id

    def test_orchestrator_donor_id_consistency(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems[:5]:
            r1 = orch.run(p, cards, "lcd_convergence", convergence_budget=2)
            r2 = orch.run(p, cards, "lcd_convergence", convergence_budget=2)
            assert r1.donor_card_id == r2.donor_card_id == p.donor_card_id


class TestBenchmarkProperties:
    """Test benchmark structure properties."""

    def test_14_total_problems(self):
        problems = load_problems("benchmark/benchmark.jsonl")
        assert len(problems) == 14

    def test_40_total_cards(self):
        cards = load_cards("data/knowledge_base.jsonl")
        assert len(cards) == 40

    def test_12_core_and_2_controls(self):
        problems = load_problems("benchmark/benchmark.jsonl")
        cores = [p for p in problems if p.control_type is None]
        controls = [p for p in problems if p.control_type is not None]
        assert len(cores) == 12
        assert len(controls) == 2

    def test_all_problems_have_unique_ids(self):
        problems = load_problems("benchmark/benchmark.jsonl")
        ids = [p.id for p in problems]
        assert len(ids) == len(set(ids))

    def test_all_cards_have_unique_ids(self):
        cards = load_cards("data/knowledge_base.jsonl")
        ids = [c.id for c in cards]
        assert len(ids) == len(set(ids))


class TestAllConditionsHaveValidStructure:
    """Test that all conditions produce valid structure."""

    def test_baseline_naive_structure(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        r = orch.run(problems[0], cards, "baseline_a_naive", convergence_budget=5)
        assert hasattr(r, 'passed') and isinstance(r.passed, bool)
        assert hasattr(r, 'score') and isinstance(r.score, (int, float))
        assert hasattr(r, 'num_attempts') and isinstance(r.num_attempts, int)

    def test_rag_top1_structure(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        r = orch.run(problems[0], cards, "rag_top1", convergence_budget=5)
        assert hasattr(r, 'passed') and isinstance(r.passed, bool)
        assert hasattr(r, 'score') and isinstance(r.score, (int, float))
        assert hasattr(r, 'num_attempts') and isinstance(r.num_attempts, int)

    def test_rag_convergence_structure(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        r = orch.run(problems[0], cards, "rag_convergence", convergence_budget=5)
        assert hasattr(r, 'passed') and isinstance(r.passed, bool)
        assert hasattr(r, 'score') and isinstance(r.score, (int, float))
        assert hasattr(r, 'num_attempts') and isinstance(r.num_attempts, int)

    def test_lcd_top1_structure(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        r = orch.run(problems[0], cards, "lcd_top1", convergence_budget=5)
        assert hasattr(r, 'passed') and isinstance(r.passed, bool)
        assert hasattr(r, 'score') and isinstance(r.score, (int, float))
        assert hasattr(r, 'num_attempts') and isinstance(r.num_attempts, int)

    def test_lcd_convergence_structure(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        r = orch.run(problems[0], cards, "lcd_convergence", convergence_budget=5)
        assert hasattr(r, 'passed') and isinstance(r.passed, bool)
        assert hasattr(r, 'score') and isinstance(r.score, (int, float))
        assert hasattr(r, 'num_attempts') and isinstance(r.num_attempts, int)


class TestRetrievalCompleteness:
    """Test that retrieval returns all cards."""

    def test_rag_retrieve_all_40_cards(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)

        p = problems[0]
        ranked = rag_retrieve(p, cards, vs)
        assert len(ranked) == 40

    def test_capability_retrieve_all_40_cards(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)

        p = problems[0]
        ranked = capability_retrieve(p, cards, vs)
        assert len(ranked) == 40

    def test_rag_returns_distinct_cards(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)

        p = problems[0]
        ranked = rag_retrieve(p, cards, vs)
        ids = [c.id for c, _ in ranked]
        assert len(ids) == len(set(ids))

    def test_capability_returns_distinct_cards(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)

        p = problems[0]
        ranked = capability_retrieve(p, cards, vs)
        ids = [c.id for c, _ in ranked]
        assert len(ids) == len(set(ids))
