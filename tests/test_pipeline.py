import inspect
import json
import tempfile
from pathlib import Path

from lcd.schema import KnowledgeCard, BenchmarkProblem, save_cards, load_cards
from lcd.vectorspace import build_vector_space
from lcd.retriever import rag_retrieve, capability_retrieve
from lcd.reasoner import get_default_reasoner, HeuristicReasoner
from lcd.pipeline import Orchestrator, CONDITIONS
from lcd.metrics import leakage_check, summarize


def _toy_cards():
    return [
        KnowledgeCard(
            id="donor", domain="biology", title="Donor",
            text="ants deposit pheromone trails while foraging for food",
            capability_tags=["reinforcing successful paths while allowing exploration of alternatives",
                              "adapting routing or choice probabilistically based on accumulated feedback"],
            mechanism_template="reinforce successful paths, evaporate stale trails, adapt routing choice over time",
            domain_terms=["pheromone", "ants", "foraging"], code_skeleton=None,
        ),
        KnowledgeCard(
            id="distractor", domain="software_engineering", title="Distractor",
            text="routing tables are computed once from a cost snapshot and cached forever without revisiting",
            capability_tags=["precompute once and cache the result"],
            mechanism_template="cache a fixed decision forever without revisiting it",
            domain_terms=[], code_skeleton=None, is_distractor=True,
        ),
    ]


def _toy_problem():
    return BenchmarkProblem(
        id="toy", title="toy",
        statement=("routing tables are computed once and cached, but costs shift over "
                   "time and routing never adapts"),
        donor_card_id="donor", baseline_a_card_id="distractor",
        harness_module="tests.fixtures.toy_harness",
    )


def test_schema_roundtrip():
    cards = _toy_cards()
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "cards.jsonl"
        save_cards(cards, path)
        loaded = load_cards(path)
    assert [c.id for c in loaded] == [c.id for c in cards]
    assert loaded[0].capability_tags == cards[0].capability_tags


def test_retriever_never_reads_domain_field():
    src = inspect.getsource(capability_retrieve)
    code_lines = [line.split("#", 1)[0] for line in src.splitlines()]
    code_only = "\n".join(code_lines)
    assert ".domain" not in code_only, "capability_retrieve must be domain-blind (found outside a comment)"


def test_capability_retrieval_can_outrank_text_retrieval_on_toy_example():
    # A minimal, hand-checkable version of the real finding: a problem
    # statement that lexically overlaps with a same-domain distractor (both
    # mention "routing tables ... computed once ... cached") gets matched to
    # that distractor by raw text similarity, while capability projection
    # (via glossary phrases like "adapting routing ... based on accumulated
    # feedback") correctly surfaces the cross-domain donor instead, even
    # though the donor's raw text ("ants", "pheromone", "foraging") shares no
    # vocabulary with the problem statement at all.
    cards = _toy_cards()
    problem = _toy_problem()
    vs = build_vector_space(cards, [problem])
    rag_ranked = [c.id for c, _ in rag_retrieve(problem, cards, vs)]
    cap_ranked = [c.id for c, _ in capability_retrieve(problem, cards, vs)]
    assert rag_ranked[0] == "distractor"
    assert cap_ranked[0] == "donor"


def test_leakage_check_flags_leaked_jargon():
    cards = {c.id: c for c in _toy_cards()}
    problem = _toy_problem()
    assert leakage_check(problem, cards) == []
    leaky_problem = BenchmarkProblem(id="leaky", title="leaky", statement="watch out for the pheromone trail",
                                      donor_card_id="donor", baseline_a_card_id="distractor",
                                      harness_module="tests.fixtures.toy_harness")
    assert "pheromone" in leakage_check(leaky_problem, cards)


def test_orchestrator_runs_all_conditions_without_crashing(tmp_path):
    # exercise the real benchmark end-to-end on one real problem per condition
    from lcd.schema import load_cards as load_real_cards, load_problems as load_real_problems
    cards = load_real_cards("data/knowledge_base.jsonl")
    problems = load_real_problems("benchmark/benchmark.jsonl")
    vs = build_vector_space(cards, problems)
    reasoner = get_default_reasoner(vs)
    assert isinstance(reasoner, HeuristicReasoner)
    orch = Orchestrator(vs, reasoner)
    problem = next(p for p in problems if p.id == "streaming_sample")
    for condition in CONDITIONS:
        result = orch.run(problem, cards, condition, convergence_budget=5)
        assert result.condition == condition
        assert result.num_attempts >= 1


def test_summarize_counts_controls_separately():
    from lcd.schema import load_cards as load_real_cards, load_problems as load_real_problems
    cards = load_real_cards("data/knowledge_base.jsonl")
    problems = load_real_problems("benchmark/benchmark.jsonl")
    vs = build_vector_space(cards, problems)
    reasoner = get_default_reasoner(vs)
    orch = Orchestrator(vs, reasoner)
    results = [orch.run(p, cards, "lcd_convergence", convergence_budget=5) for p in problems]
    summary = summarize(results, problems)
    assert summary.n_core == 12  # 14 problems minus 2 controls
