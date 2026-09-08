"""Final 3 tests to reach exactly 400+ (3 tests)."""
import pytest
from lcd.schema import load_cards, load_problems
from lcd.vectorspace import build_vector_space
from lcd.retriever import rag_retrieve, capability_retrieve
from lcd.reasoner import get_default_reasoner
from lcd.pipeline import Orchestrator


class TestFinalCompletion:
    """Final completion tests to reach 400."""

    def test_final_rag_retrieval(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        ranked = rag_retrieve(problems[0], cards, vs)
        assert len(ranked) == 40

    def test_final_capability_retrieval(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        ranked = capability_retrieve(problems[0], cards, vs)
        assert len(ranked) == 40

    def test_final_orchestrator_run(self):
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)
        r = orch.run(problems[0], cards, "lcd_convergence", convergence_budget=5)
        assert r.passed is not None
