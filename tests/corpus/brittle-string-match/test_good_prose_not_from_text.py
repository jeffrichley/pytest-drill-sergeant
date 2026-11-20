"""Near-misses: long string literals that aren't compared with rendered text.
Analysed, never run."""

import pytest
from app import Profile, send, summarize

pytestmark = pytest.mark.unit


def test_bio_is_stored_as_given():
    profile = Profile(bio="Loves long walks on the beach and quiet evenings")
    assert profile.bio == "Loves long walks on the beach and quiet evenings"


def test_prose_used_as_input(outbox):
    message = "Your order has shipped and will arrive on Tuesday"
    send(message)
    assert outbox == [message]


def test_summary_against_a_variable(expected_summary):
    assert summarize("a b c d e") == expected_summary


def test_text_compared_with_a_variable(capsys, expected_output):
    summarize("a b c d e")
    assert capsys.readouterr().out == expected_output
