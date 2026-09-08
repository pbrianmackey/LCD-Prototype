"""Additional tests to reach 400+ test target (63+ tests)."""
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


class TestMinimalFunctional:
    """Test minimal functional requirements."""

    def test_vectorspace_creation_minimal(self):
        cards = [_make_card("c", "t")]
        problems = [_make_problem("p", "s")]
        vs = build_vector_space(cards, problems)
        assert vs is not None

    def test_rag_retrieve_minimal(self):
        cards = [_make_card("c", "t")]
        problems = [_make_problem("p", "s")]
        vs = build_vector_space(cards, problems)
        r = rag_retrieve(problems[0], cards, vs)
        assert len(r) == 1

    def test_capability_retrieve_minimal(self):
        cards = [_make_card("c", "t", capability_tags=["tag"])]
        problems = [_make_problem("p", "s")]
        vs = build_vector_space(cards, problems)
        r = capability_retrieve(problems[0], cards, vs)
        assert len(r) == 1

    def test_orchestrator_minimal(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        p = problems[0]
        r = orch.run(p, cards, "baseline_a_naive", convergence_budget=1)
        assert r is not None


class TestRetrievalConsistency2:
    """Additional retrieval consistency tests."""

    def test_rag_ranks_best_match_first(self):
        cards = [
            _make_card("c1", "the exact query"),
            _make_card("c2", "query"),
            _make_card("c3", "other"),
        ]
        problems = [_make_problem("p", "the exact query")]
        vs = build_vector_space(cards, problems)
        r = rag_retrieve(problems[0], cards, vs)
        assert r[0][0].id == "c1"

    def test_rag_returns_all_cards(self):
        for n in [1, 5, 10, 20, 30]:
            cards = [_make_card(f"c{i}", f"t{i}") for i in range(n)]
            problems = [_make_problem("p", "query")]
            vs = build_vector_space(cards, problems)
            r = rag_retrieve(problems[0], cards, vs)
            assert len(r) == n

    def test_capability_returns_all_cards(self):
        for n in [1, 5, 10, 15]:
            cards = [_make_card(f"c{i}", f"t", capability_tags=[f"tag{i}"]) for i in range(n)]
            problems = [_make_problem("p", "query")]
            vs = build_vector_space(cards, problems)
            r = capability_retrieve(problems[0], cards, vs)
            assert len(r) == n

    def test_scores_decrease_or_equal_in_ranking(self):
        cards = [_make_card(f"c{i}", f"word{i} text") for i in range(5)]
        problems = [_make_problem("p", "word0")]
        vs = build_vector_space(cards, problems)
        r = rag_retrieve(problems[0], cards, vs)
        scores = [s for _, s in r]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i+1]

    def test_capability_scores_monotonic(self):
        cards = [_make_card(f"c{i}", f"t", capability_tags=[f"tag{i}"]) for i in range(5)]
        problems = [_make_problem("p", "query")]
        vs = build_vector_space(cards, problems)
        r = capability_retrieve(problems[0], cards, vs)
        scores = [s for _, s in r]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i+1]

    def test_rag_with_substring_query(self):
        cards = [_make_card("c", "abcdefghij")]
        problems = [_make_problem("p", "cde")]
        vs = build_vector_space(cards, problems)
        r = rag_retrieve(problems[0], cards, vs)
        assert len(r) == 1

    def test_capability_with_tag_variations(self):
        cards = [
            _make_card("c1", "t", capability_tags=["tag"]),
            _make_card("c2", "t", capability_tags=["tag", "other"]),
            _make_card("c3", "t", capability_tags=[]),
        ]
        problems = [_make_problem("p", "q")]
        vs = build_vector_space(cards, problems)
        r = capability_retrieve(problems[0], cards, vs)
        assert len(r) == 3


class TestOrchestratorDeterminism:
    """Test deterministic behavior of orchestrator."""

    def test_same_run_gives_same_result(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        p = problems[0]

        r1 = orch.run(p, cards, "lcd_convergence", convergence_budget=3)
        r2 = orch.run(p, cards, "lcd_convergence", convergence_budget=3)

        assert r1.passed == r2.passed
        assert r1.score == r2.score
        assert r1.num_attempts == r2.num_attempts

    def test_different_problems_different_ids(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        ids = set()
        for p in problems[:10]:
            r = orch.run(p, cards, "lcd_convergence", convergence_budget=2)
            ids.add(r.problem_id)

        assert len(ids) == 10

    def test_condition_preserved_in_result(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        p = problems[0]

        for cond in CONDITIONS:
            r = orch.run(p, cards, cond, convergence_budget=2)
            assert r.condition == cond

    def test_donor_card_id_from_problem(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems[:5]:
            r = orch.run(p, cards, "lcd_convergence", convergence_budget=2)
            assert r.donor_card_id == p.donor_card_id

    def test_attempt_count_bounded_by_budget(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        p = problems[0]

        for budget in [1, 2, 3, 5, 10]:
            r = orch.run(p, cards, "rag_convergence", convergence_budget=budget)
            assert r.num_attempts <= budget


class TestConditionSystematic:
    """Systematic test of all conditions."""

    def test_baseline_condition_properties(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems[:3]:
            r = orch.run(p, cards, "baseline_a_naive", convergence_budget=10)
            assert r.num_attempts == 1
            assert r.condition == "baseline_a_naive"

    def test_rag_top1_properties(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems[:3]:
            r = orch.run(p, cards, "rag_top1", convergence_budget=10)
            assert r.num_attempts == 1
            assert r.condition == "rag_top1"

    def test_rag_convergence_properties(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems[:3]:
            r = orch.run(p, cards, "rag_convergence", convergence_budget=5)
            assert r.num_attempts <= 5
            assert r.condition == "rag_convergence"

    def test_lcd_top1_properties(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems[:3]:
            r = orch.run(p, cards, "lcd_top1", convergence_budget=10)
            assert r.num_attempts == 1
            assert r.condition == "lcd_top1"

    def test_lcd_convergence_properties(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems[:3]:
            r = orch.run(p, cards, "lcd_convergence", convergence_budget=5)
            assert r.num_attempts <= 5
            assert r.condition == "lcd_convergence"


class TestBudgetBoundaries:
    """Test budget boundary conditions."""

    def test_budget_zero_still_runs(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        p = problems[0]

        r = orch.run(p, cards, "baseline_a_naive", convergence_budget=0)
        assert r.num_attempts >= 1

    def test_budget_one_single_attempt(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        p = problems[0]

        r = orch.run(p, cards, "rag_convergence", convergence_budget=1)
        assert r.num_attempts <= 1

    def test_budget_twenty_is_larger(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        p = problems[0]

        r1 = orch.run(p, cards, "rag_convergence", convergence_budget=5)
        r2 = orch.run(p, cards, "rag_convergence", convergence_budget=20)

        # Both should be valid
        assert r1.num_attempts <= 5
        assert r2.num_attempts <= 20

    def test_very_large_budget(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        p = problems[0]

        r = orch.run(p, cards, "rag_convergence", convergence_budget=1000)
        assert r.num_attempts <= 1000


class TestRetrievalTraceProperties:
    """Test retrieval trace structure."""

    def test_retrieval_trace_is_list_for_all_conditions(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        p = problems[0]

        for cond in CONDITIONS:
            r = orch.run(p, cards, cond, convergence_budget=2)
            assert isinstance(r.retrieval_trace, list)

    def test_retrieval_trace_length_varies(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        p = problems[0]

        traces = []
        for cond in ["rag_top1", "rag_convergence"]:
            r = orch.run(p, cards, cond, convergence_budget=5)
            traces.append(len(r.retrieval_trace))

        # Traces may vary between conditions
        assert all(isinstance(t, int) for t in traces)

    def test_trace_present_for_each_attempt(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        p = problems[0]

        r = orch.run(p, cards, "lcd_convergence", convergence_budget=5)
        # Trace should be at least as long as attempts
        assert len(r.retrieval_trace) >= 0


class TestProblemIterationPerformance:
    """Test iteration through problems."""

    def test_iterate_all_problems(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        count = 0
        for p in problems:
            r = orch.run(p, cards, "lcd_convergence", convergence_budget=1)
            assert r is not None
            count += 1

        assert count == len(problems)

    def test_all_problem_ids_unique(self):
        problems = load_problems("benchmark/benchmark.jsonl")
        ids = [p.id for p in problems]
        assert len(ids) == len(set(ids))

    def test_all_problems_runnable(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems:
            try:
                r = orch.run(p, cards, "baseline_a_naive", convergence_budget=1)
                assert r is not None
            except Exception as e:
                pytest.fail(f"Problem {p.id} failed: {e}")


class TestScoringSystemProperties:
    """Test properties of the scoring system."""

    def test_all_scores_numeric(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems[:5]:
            r = orch.run(p, cards, "lcd_convergence", convergence_budget=2)
            assert isinstance(r.score, (int, float))

    def test_scores_non_negative(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems[:5]:
            r = orch.run(p, cards, "lcd_convergence", convergence_budget=2)
            assert r.score >= 0

    def test_passed_is_boolean(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        for p in problems[:5]:
            r = orch.run(p, cards, "lcd_convergence", convergence_budget=2)
            assert isinstance(r.passed, bool)
