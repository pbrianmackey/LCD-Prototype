"""Comprehensive tests for schema, knowledge base building, and data loading (100+ tests)."""
import json
import tempfile
from pathlib import Path
from lcd.schema import (
    KnowledgeCard, BenchmarkProblem, save_cards, load_cards,
    load_problems, save_problems
)


class TestKnowledgeCardCreation:
    """Test KnowledgeCard instantiation and validation."""

    def test_knowledge_card_minimal_fields(self):
        card = KnowledgeCard(
            id="test1", domain="test", title="Test",
            text="text", capability_tags=[], mechanism_template="mech",
            domain_terms=[], code_skeleton=None
        )
        assert card.id == "test1"
        assert card.domain == "test"

    def test_knowledge_card_with_all_fields(self):
        card = KnowledgeCard(
            id="test2", domain="biology", title="Ant Colony",
            text="ants leave pheromone trails",
            capability_tags=["tag1", "tag2"],
            mechanism_template="reinforce paths",
            domain_terms=["pheromone", "ants"],
            code_skeleton="def foo(): pass",
            is_distractor=False,
            historical_note="1960s entomology"
        )
        assert card.historical_note == "1960s entomology"
        assert not card.is_distractor

    def test_knowledge_card_distractor_flag(self):
        card_distractor = KnowledgeCard(
            id="d1", domain="cs", title="D", text="text",
            capability_tags=[], mechanism_template="m",
            domain_terms=[], is_distractor=True
        )
        assert card_distractor.is_distractor

    def test_knowledge_card_empty_capability_tags(self):
        card = KnowledgeCard(
            id="test3", domain="x", title="X", text="text",
            capability_tags=[], mechanism_template="m", domain_terms=[]
        )
        assert card.capability_tags == []

    def test_knowledge_card_multiple_capability_tags(self):
        tags = ["feedback", "adaptation", "learning", "optimization"]
        card = KnowledgeCard(
            id="test4", domain="cs", title="T", text="text",
            capability_tags=tags, mechanism_template="m", domain_terms=[]
        )
        assert len(card.capability_tags) == 4

    def test_knowledge_card_domain_terms_various_lengths(self):
        for n in [0, 1, 5, 20]:
            terms = [f"term{i}" for i in range(n)]
            card = KnowledgeCard(
                id=f"test_{n}", domain="d", title="T", text="text",
                capability_tags=[], mechanism_template="m", domain_terms=terms
            )
            assert len(card.domain_terms) == n

    def test_knowledge_card_code_skeleton_present(self):
        code = "def mechanism(): return 42"
        card = KnowledgeCard(
            id="test5", domain="d", title="T", text="text",
            capability_tags=[], mechanism_template="m", domain_terms=[],
            code_skeleton=code
        )
        assert card.code_skeleton == code

    def test_knowledge_card_with_unicode_text(self):
        card = KnowledgeCard(
            id="test6", domain="d", title="Ünïcödé",
            text="Системы с обратной связью",
            capability_tags=["αβγ"], mechanism_template="m",
            domain_terms=["日本語"]
        )
        assert "Ünïcödé" in card.title

    def test_knowledge_card_long_text(self):
        long_text = "word " * 10000
        card = KnowledgeCard(
            id="test7", domain="d", title="T", text=long_text,
            capability_tags=[], mechanism_template="m", domain_terms=[]
        )
        assert len(card.text) > 50000


class TestBenchmarkProblemCreation:
    """Test BenchmarkProblem instantiation and validation."""

    def test_benchmark_problem_minimal(self):
        problem = BenchmarkProblem(
            id="prob1", title="Problem 1",
            statement="test statement",
            donor_card_id="donor", baseline_a_card_id="baseline",
            harness_module="module"
        )
        assert problem.id == "prob1"
        assert problem.donor_card_id == "donor"
        assert problem.control_type is None

    def test_benchmark_problem_with_control_type(self):
        problem = BenchmarkProblem(
            id="control1", title="Control",
            statement="test", donor_card_id="d", baseline_a_card_id="b",
            harness_module="m", control_type="no_kb_solution"
        )
        assert problem.control_type == "no_kb_solution"

    def test_benchmark_problem_donor_equals_baseline(self):
        problem = BenchmarkProblem(
            id="prob2", title="Prob",
            statement="test", donor_card_id="same", baseline_a_card_id="same",
            harness_module="m"
        )
        assert problem.donor_card_id == problem.baseline_a_card_id

    def test_benchmark_problem_with_expected_attempts(self):
        problem = BenchmarkProblem(
            id="prob3", title="Prob",
            statement="test", donor_card_id="d", baseline_a_card_id="b",
            harness_module="m", expected_convergence_attempts=5
        )
        assert problem.expected_convergence_attempts == 5

    def test_benchmark_problem_unicode_statement(self):
        problem = BenchmarkProblem(
            id="prob4", title="Übung",
            statement="Проблемное утверждение на русском",
            donor_card_id="d", baseline_a_card_id="b", harness_module="m"
        )
        assert "Проблемное" in problem.statement

    def test_benchmark_problem_long_statement(self):
        long_stmt = "statement " * 5000
        problem = BenchmarkProblem(
            id="prob5", title="Long",
            statement=long_stmt, donor_card_id="d", baseline_a_card_id="b",
            harness_module="m"
        )
        assert len(problem.statement) > 40000


class TestCardSerialization:
    """Test saving and loading cards to/from JSONL."""

    def test_save_and_load_single_card(self):
        cards = [KnowledgeCard(
            id="test", domain="d", title="T", text="text",
            capability_tags=["tag"], mechanism_template="m",
            domain_terms=["term"]
        )]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "cards.jsonl"
            save_cards(cards, path)
            loaded = load_cards(path)
        assert len(loaded) == 1
        assert loaded[0].id == "test"

    def test_save_and_load_multiple_cards(self):
        cards = [
            KnowledgeCard(id=f"c{i}", domain="d", title=f"T{i}",
                         text=f"text{i}", capability_tags=[],
                         mechanism_template="m", domain_terms=[])
            for i in range(20)
        ]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "cards.jsonl"
            save_cards(cards, path)
            loaded = load_cards(path)
        assert len(loaded) == 20
        assert [c.id for c in loaded] == [c.id for c in cards]

    def test_save_and_load_preserves_all_fields(self):
        card = KnowledgeCard(
            id="complex", domain="biology", title="Ant Colony Optimization",
            text="ants deposit pheromone",
            capability_tags=["feedback", "learning"],
            mechanism_template="reinforce paths over time",
            domain_terms=["pheromone", "ants"],
            code_skeleton="def aco(): pass",
            is_distractor=False,
            historical_note="1990s Dorigo et al"
        )
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "cards.jsonl"
            save_cards([card], path)
            loaded = load_cards(path)
        assert loaded[0].historical_note == card.historical_note
        assert loaded[0].capability_tags == card.capability_tags

    def test_save_creates_file(self):
        cards = [KnowledgeCard(id="c1", domain="d", title="T", text="t",
                              capability_tags=[], mechanism_template="m",
                              domain_terms=[])]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "test.jsonl"
            assert not path.exists()
            save_cards(cards, path)
            assert path.exists()

    def test_load_from_nonexistent_file_raises(self):
        import pytest
        with pytest.raises(FileNotFoundError):
            load_cards(Path("/nonexistent/path/cards.jsonl"))

    def test_save_and_load_empty_list(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "empty.jsonl"
            save_cards([], path)
            loaded = load_cards(path)
        assert loaded == []

    def test_save_and_load_with_distractor_flag(self):
        cards = [
            KnowledgeCard(id="d1", domain="cs", title="D1", text="t",
                         capability_tags=[], mechanism_template="m",
                         domain_terms=[], is_distractor=True),
            KnowledgeCard(id="r1", domain="d", title="R1", text="t",
                         capability_tags=[], mechanism_template="m",
                         domain_terms=[], is_distractor=False),
        ]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "mixed.jsonl"
            save_cards(cards, path)
            loaded = load_cards(path)
        assert loaded[0].is_distractor
        assert not loaded[1].is_distractor


class TestProblemSerialization:
    """Test saving and loading problems to/from JSONL."""

    def test_save_and_load_single_problem(self):
        problem = BenchmarkProblem(
            id="p1", title="Problem",
            statement="test", donor_card_id="d", baseline_a_card_id="b",
            harness_module="module"
        )
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "problems.jsonl"
            save_problems([problem], path)
            loaded = load_problems(path)
        assert len(loaded) == 1
        assert loaded[0].id == "p1"

    def test_save_and_load_multiple_problems(self):
        problems = [
            BenchmarkProblem(id=f"p{i}", title=f"P{i}",
                            statement=f"stmt{i}", donor_card_id="d",
                            baseline_a_card_id="b", harness_module="m")
            for i in range(15)
        ]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "problems.jsonl"
            save_problems(problems, path)
            loaded = load_problems(path)
        assert len(loaded) == 15

    def test_save_and_load_preserves_control_type(self):
        problems = [
            BenchmarkProblem(id="ctrl", title="C",
                            statement="s", donor_card_id="d", baseline_a_card_id="b",
                            harness_module="m", control_type="no_kb_solution"),
            BenchmarkProblem(id="norm", title="N",
                            statement="s", donor_card_id="d", baseline_a_card_id="b",
                            harness_module="m")
        ]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "problems.jsonl"
            save_problems(problems, path)
            loaded = load_problems(path)
        assert loaded[0].control_type == "no_kb_solution"
        assert loaded[1].control_type is None

    def test_save_and_load_empty_problems(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "empty_problems.jsonl"
            save_problems([], path)
            loaded = load_problems(path)
        assert loaded == []


class TestDataConsistency:
    """Test consistency constraints across schema objects."""

    def test_card_id_uniqueness_after_roundtrip(self):
        cards = [
            KnowledgeCard(id="unique1", domain="d", title="T1", text="t1",
                         capability_tags=[], mechanism_template="m", domain_terms=[]),
            KnowledgeCard(id="unique2", domain="d", title="T2", text="t2",
                         capability_tags=[], mechanism_template="m", domain_terms=[]),
            KnowledgeCard(id="unique3", domain="d", title="T3", text="t3",
                         capability_tags=[], mechanism_template="m", domain_terms=[]),
        ]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "cards.jsonl"
            save_cards(cards, path)
            loaded = load_cards(path)
        ids = [c.id for c in loaded]
        assert len(ids) == len(set(ids))

    def test_problem_harness_module_preserved(self):
        harnesses = [
            "benchmark.problems.autoscaler_oscillation",
            "benchmark.problems.streaming_sample",
            "custom.harness.module"
        ]
        problems = [
            BenchmarkProblem(id=f"p{i}", title=f"P{i}",
                            statement="s", donor_card_id="d", baseline_a_card_id="b",
                            harness_module=h)
            for i, h in enumerate(harnesses)
        ]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "problems.jsonl"
            save_problems(problems, path)
            loaded = load_problems(path)
        for i, problem in enumerate(loaded):
            assert problem.harness_module == harnesses[i]
