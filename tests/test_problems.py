"""
Regression tests encoding each benchmark problem's calibration guarantee:
the donor mechanism passes, the same-domain baseline/distractor fails --
except the two control problems, which have their own documented contract.
These are the same facts asserted in each benchmark/problems/*.py's
__main__ block, just collected into one pytest-discoverable file so
`pytest tests/` catches a calibration regression (e.g. someone tightening a
threshold and breaking a previously-passing donor) automatically.
"""
import importlib

import pytest

from lcd.schema import load_problems

ROOT_PROBLEMS = load_problems("benchmark/benchmark.jsonl")


@pytest.mark.parametrize("problem", ROOT_PROBLEMS, ids=[p.id for p in ROOT_PROBLEMS])
def test_problem_calibration(problem):
    harness = importlib.import_module(problem.harness_module)

    if problem.control_type == "no_kb_solution":
        for card_id, factory in harness.CARD_ADAPTERS.items():
            passed, _score, detail = harness.evaluate(factory())
            assert not passed, f"{problem.id}/{card_id} unexpectedly passed an impossible problem: {detail}"
        return

    donor_factory = harness.CARD_ADAPTERS[problem.donor_card_id]
    passed, _score, detail = harness.evaluate(donor_factory())
    assert passed, f"{problem.id}: donor card {problem.donor_card_id} should pass but didn't: {detail}"

    if problem.baseline_a_card_id != problem.donor_card_id:
        baseline_factory = harness.CARD_ADAPTERS[problem.baseline_a_card_id]
        passed, _score, detail = harness.evaluate(baseline_factory())
        assert not passed, (
            f"{problem.id}: same-domain baseline {problem.baseline_a_card_id} "
            f"should fail but passed: {detail}"
        )
