"""Oracle test for Q4 -- instructor/TA use only, never pushed to a
student repo."""
import pytest

from q4_consensus import consensus_vote


def test_returns_the_winner_when_it_has_a_strict_majority():
    assert consensus_vote(["billing", "billing", "technical"]) == "billing"


def test_unanimous_vote():
    assert consensus_vote(["shipping", "shipping", "shipping"]) == "shipping"


def test_three_way_split_has_no_consensus():
    assert consensus_vote(["billing", "technical", "shipping"]) == "no_consensus"


def test_exact_two_way_tie_has_no_consensus():
    assert consensus_vote(["billing", "technical"]) == "no_consensus"


def test_single_label_is_a_strict_majority_of_one():
    assert consensus_vote(["billing"]) == "billing"


def test_empty_list_raises_value_error():
    with pytest.raises(ValueError):
        consensus_vote([])


def test_grading_does_not_require_any_output_file_on_disk(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # empty directory -- no vote log here
    assert consensus_vote(["a", "a", "b"]) == "a"
