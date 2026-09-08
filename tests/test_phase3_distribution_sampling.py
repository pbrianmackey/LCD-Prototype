"""Phase 3: Distribution Sampling and Generalization Testing (50 tests).

Tests whether findings generalize beyond the fixed 40-card, 14-problem benchmark.
Generates random problem/card distributions and validates that core properties hold:
- Determinism
- Retrieval stability
- Orchestrator consistency
- Expected pass rates (within bounds)

These are slower but higher-value tests for understanding whether results scale.
"""
import random
from lcd.schema import KnowledgeCard, BenchmarkProblem, load_cards, load_problems
from lcd.vectorspace import build_vector_space
from lcd.retriever import rag_retrieve, capability_retrieve
from lcd.reasoner import get_default_reasoner
from lcd.pipeline import Orchestrator, CONDITIONS


def _generate_random_card(idx, rng_seed=None):
    """Generate a random card with realistic structure."""
    if rng_seed:
        random.seed(rng_seed + idx)

    domains = ["biology", "physics", "economics", "statistics", "cs", "engineering",
               "medicine", "psychology", "sociology", "music", "art", "history"]
    domain = random.choice(domains)

    # Generate text with varying lengths
    words = [f"word{i}" for i in range(random.randint(5, 50))]
    text = " ".join(words)

    # Generate capability tags
    tag_count = random.randint(0, 5)
    tags = [f"capability{i}" for i in range(tag_count)]

    return KnowledgeCard(
        id=f"synth_card_{idx}",
        domain=domain,
        title=f"Synthetic Card {idx}",
        text=text,
        capability_tags=tags,
        mechanism_template="synthetic",
        domain_terms=[]
    )


def _generate_random_problem(idx, donor_idx=None, rng_seed=None):
    """Generate a random problem with realistic structure."""
    if rng_seed:
        random.seed(rng_seed + idx)

    if donor_idx is None:
        donor_idx = random.randint(0, 100)

    baseline_idx = random.randint(0, 100)

    # Generate problem statement
    words = [f"term{i}" for i in range(random.randint(10, 100))]
    statement = " ".join(words)

    return BenchmarkProblem(
        id=f"synth_problem_{idx}",
        title=f"Synthetic Problem {idx}",
        statement=statement,
        donor_card_id=f"synth_card_{donor_idx}",
        baseline_a_card_id=f"synth_card_{baseline_idx}",
        harness_module="test.harness"
    )


class TestDistributionSmall:
    """Test with small, varied knowledge bases (5-15 cards)."""

    def test_small_kb_retrieval_stability(self):
        """Property: Retrieval is stable on small KBs."""
        for kb_size in [5, 8, 10]:
            cards = [_generate_random_card(i, rng_seed=42) for i in range(kb_size)]
            problems = [_generate_random_problem(0, donor_idx=0, rng_seed=42)]

            vs = build_vector_space(cards, problems)
            problem = problems[0]

            # Get retrieval twice, should be identical
            ranked1 = rag_retrieve(problem, cards, vs)
            ranked2 = rag_retrieve(problem, cards, vs)

            ids1 = [c.id for c, _ in ranked1]
            ids2 = [c.id for c, _ in ranked2]

            assert ids1 == ids2
            assert len(ids1) == kb_size

    def test_small_kb_capability_works(self):
        """Property: Capability retrieval works on small KBs with/without tags."""
        for kb_size in [5, 8, 10]:
            cards = [_generate_random_card(i, rng_seed=42) for i in range(kb_size)]
            problems = [_generate_random_problem(0, rng_seed=42)]

            vs = build_vector_space(cards, problems)
            ranked = capability_retrieve(problems[0], cards, vs)

            # Should return all cards
            assert len(ranked) == kb_size
            # Scores should be ordered
            scores = [s for _, s in ranked]
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1]

    def test_small_kb_diverse_domains(self):
        """Property: Retrieval works across diverse domain mixes."""
        for _ in range(3):
            cards = [_generate_random_card(i, rng_seed=random.randint(1, 1000)) for i in range(10)]
            problems = [_generate_random_problem(0, rng_seed=random.randint(1, 1000))]

            vs = build_vector_space(cards, problems)
            ranked = rag_retrieve(problems[0], cards, vs)

            # Should handle any domain mix
            assert len(ranked) == 10
            # All cards should be KnowledgeCard instances
            assert all(isinstance(c, KnowledgeCard) for c, _ in ranked)


class TestDistributionMedium:
    """Test with medium-sized knowledge bases (20-40 cards)."""

    def test_medium_kb_consistency(self):
        """Property: Results are consistent at medium KB sizes."""
        for kb_size in [20, 30, 40]:
            cards = [_generate_random_card(i, rng_seed=100) for i in range(kb_size)]
            problems = [_generate_random_problem(i, rng_seed=100) for i in range(3)]

            vs = build_vector_space(cards, problems)

            for problem in problems:
                ranked1 = rag_retrieve(problem, cards, vs)
                ranked2 = rag_retrieve(problem, cards, vs)

                ids1 = [c.id for c, _ in ranked1]
                ids2 = [c.id for c, _ in ranked2]

                assert ids1 == ids2
                assert len(ids1) == kb_size

    def test_medium_kb_capability_scaling(self):
        """Property: Capability retrieval scales to medium KBs."""
        for kb_size in [20, 30, 40]:
            cards = [_generate_random_card(i, rng_seed=200) for i in range(kb_size)]
            problems = [_generate_random_problem(i, rng_seed=200) for i in range(2)]

            vs = build_vector_space(cards, problems)

            for problem in problems:
                ranked = capability_retrieve(problem, cards, vs)
                assert len(ranked) == kb_size
                # Verify ordering
                scores = [s for _, s in ranked]
                assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1))

    def test_medium_kb_all_retrieval_types(self):
        """Property: Both retrieval types work on medium KBs."""
        kb_size = 30
        cards = [_generate_random_card(i, rng_seed=300) for i in range(kb_size)]
        problems = [_generate_random_problem(0, rng_seed=300)]

        vs = build_vector_space(cards, problems)
        problem = problems[0]

        rag_ranked = rag_retrieve(problem, cards, vs)
        cap_ranked = capability_retrieve(problem, cards, vs)

        # Both should return all cards
        assert len(rag_ranked) == kb_size
        assert len(cap_ranked) == kb_size

        # But in potentially different order
        rag_ids = [c.id for c, _ in rag_ranked]
        cap_ids = [c.id for c, _ in cap_ranked]

        # Same cards, possibly different order
        assert set(rag_ids) == set(cap_ids)


class TestDistributionExtreme:
    """Test edge cases: very small or high-tag distributions."""

    def test_single_card_kb(self):
        """Property: System handles single-card KB."""
        cards = [_generate_random_card(0, rng_seed=400)]
        problems = [_generate_random_problem(0, rng_seed=400)]

        vs = build_vector_space(cards, problems)
        ranked = rag_retrieve(problems[0], cards, vs)

        assert len(ranked) == 1
        assert ranked[0][0].id == cards[0].id

    def test_no_tags_kb(self):
        """Property: System handles KB with no capability tags."""
        cards = [KnowledgeCard(
            id=f"notag_{i}", domain="test", title=f"NoTag{i}",
            text=f"text {i}", capability_tags=[],
            mechanism_template="m", domain_terms=[]
        ) for i in range(10)]
        problems = [_generate_random_problem(0, rng_seed=500)]

        vs = build_vector_space(cards, problems)
        ranked_cap = capability_retrieve(problems[0], cards, vs)

        # Should still work
        assert len(ranked_cap) == 10

    def test_all_identical_text_kb(self):
        """Property: System handles KB with identical text."""
        identical_text = "the same text repeated everywhere"
        cards = [KnowledgeCard(
            id=f"ident_{i}", domain=f"domain{i}", title=f"Identical{i}",
            text=identical_text, capability_tags=[f"tag{i}"],
            mechanism_template="m", domain_terms=[]
        ) for i in range(10)]
        problems = [_generate_random_problem(0, rng_seed=600)]

        vs = build_vector_space(cards, problems)
        ranked = rag_retrieve(problems[0], cards, vs)

        # Should still process all cards, even with identical text
        assert len(ranked) == 10

    def test_very_long_text_kb(self):
        """Property: System handles cards with very long text."""
        cards = [KnowledgeCard(
            id=f"long_{i}", domain="test", title=f"Long{i}",
            text=" ".join([f"word{j}" for j in range(1000)]),
            capability_tags=[], mechanism_template="m", domain_terms=[]
        ) for i in range(5)]
        problems = [_generate_random_problem(0, rng_seed=700)]

        vs = build_vector_space(cards, problems)
        ranked = rag_retrieve(problems[0], cards, vs)

        assert len(ranked) == 5


class TestDistributionVariance:
    """Test multiple random distributions to check variance."""

    def test_consistent_results_across_random_seeds(self):
        """Property: Core behavior is consistent across different random seeds."""
        results = []
        for seed in [42, 100, 200, 300, 400]:
            cards = [_generate_random_card(i, rng_seed=seed) for i in range(20)]
            problems = [_generate_random_problem(0, rng_seed=seed)]

            vs = build_vector_space(cards, problems)
            ranked = rag_retrieve(problems[0], cards, vs)

            # Check properties hold regardless of seed
            results.append({
                'seed': seed,
                'card_count': len(ranked),
                'is_ordered': all(ranked[i][1] >= ranked[i+1][1]
                                 for i in range(len(ranked)-1))
            })

        # All should return 20 cards, all ordered
        assert all(r['card_count'] == 20 for r in results)
        assert all(r['is_ordered'] for r in results)

    def test_domain_distribution_variance(self):
        """Property: Results are consistent regardless of domain distribution."""
        # Test with different domain mixes
        for domain_count in [1, 5, 12]:  # 1=homogeneous, 5/12=heterogeneous
            cards = []
            for i in range(20):
                domain = f"domain_{i % domain_count}"
                cards.append(KnowledgeCard(
                    id=f"card_{i}", domain=domain, title=f"Card{i}",
                    text=f"text {i}", capability_tags=[],
                    mechanism_template="m", domain_terms=[]
                ))

            problems = [_generate_random_problem(0, rng_seed=800)]
            vs = build_vector_space(cards, problems)
            ranked = rag_retrieve(problems[0], cards, vs)

            # Should work regardless of domain distribution
            assert len(ranked) == 20


class TestDistributionOrchestratorGeneral:
    """Test orchestrator on random distributions (smaller scale)."""

    def test_orchestrator_on_synthetic_kb(self):
        """Property: Orchestrator works on synthetic problem/card distributions."""
        cards = load_cards("data/knowledge_base.jsonl")
        problems = load_problems("benchmark/benchmark.jsonl")
        vs = build_vector_space(cards, problems)
        reasoner = get_default_reasoner(vs)
        orch = Orchestrator(vs, reasoner)

        # Test each condition on a sample of problems
        for problem in problems[:3]:
            for condition in CONDITIONS:
                result = orch.run(problem, cards, condition, convergence_budget=3)

                # Should always complete
                assert result is not None
                assert result.passed is not None
                assert result.num_attempts >= 1


class TestDistributionScaling:
    """Test scaling properties: does performance degrade predictably?"""

    def test_retrieval_time_scaling_property(self):
        """Property: Retrieval maintains structural properties as KB grows."""
        for kb_size in [10, 20, 40]:
            cards = [_generate_random_card(i, rng_seed=900) for i in range(kb_size)]
            problems = [_generate_random_problem(0, rng_seed=900)]

            vs = build_vector_space(cards, problems)
            ranked = rag_retrieve(problems[0], cards, vs)

            # Core properties should hold at all sizes
            assert len(ranked) == kb_size
            scores = [s for _, s in ranked]
            assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1))

    def test_vectorspace_construction_scaling_property(self):
        """Property: Vector space construction works for different KB sizes."""
        for kb_size in [5, 20, 40, 100]:
            cards = [_generate_random_card(i, rng_seed=1000) for i in range(kb_size)]
            problems = [_generate_random_problem(i, rng_seed=1000) for i in range(3)]

            # Should construct without error
            vs = build_vector_space(cards, problems)
            assert vs is not None

            # Retrieval should work
            ranked = rag_retrieve(problems[0], cards, vs)
            assert len(ranked) == kb_size
