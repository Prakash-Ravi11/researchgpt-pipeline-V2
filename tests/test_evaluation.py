import pytest

from pipeline.diagnostics import earliest_loss
from pipeline.evaluation import score_tuples

pytestmark = pytest.mark.unit


def test_earliest_loss_does_not_treat_missing_observations_as_success():
    out = earliest_loss({"acquisition": True, "parsing": False})
    assert out["earliest_confirmed_loss"] == "parsing"
    assert not out["causal_earliest_established"]
    assert out["unknown_prior_stages"] == ["representation"]


def test_complete_tuple_scoring_requires_dataset_and_condition():
    fact = {"subject": "Ours", "dataset": "A", "metric": "Dice", "value": "91.4", "setting": "test"}
    wrong = {**fact, "setting": "validation"}
    score = score_tuples([fact], [fact, wrong])
    assert score["tuple_precision"] == .5 and score["tuple_recall"] == 1
    assert score["unsupported_claim_rate"] == .5
    empty = score_tuples([fact], [])
    assert empty["tuple_precision"] is None and empty["tuple_recall"] == 0
