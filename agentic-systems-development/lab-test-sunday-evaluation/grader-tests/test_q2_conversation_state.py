# docs/labs/lab-test-sunday-source/test_q2_conversation_state.py
"""Oracle test for Q2 -- instructor/TA use only, never pushed to a
student repo. Purely offline: append_turn takes no network dependency,
per the test's own name -- the live call the question also asks for is
never part of grading."""
import pytest

from q2_conversation_state import append_turn


def test_appends_a_well_formed_turn():
    history = [{"role": "system", "content": "You are helpful."}]
    result = append_turn(history, "user", "hello")
    assert result == [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "hello"},
    ]


def test_does_not_mutate_the_original_history():
    history = [{"role": "system", "content": "You are helpful."}]
    append_turn(history, "user", "hello")
    assert history == [{"role": "system", "content": "You are helpful."}]


def test_rejects_an_unknown_role():
    with pytest.raises(ValueError):
        append_turn([], "narrator", "hello")


def test_grading_does_not_require_any_output_file_on_disk(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # empty directory -- no conversation.json here
    result = append_turn([], "user", "hi")
    assert result == [{"role": "user", "content": "hi"}]
