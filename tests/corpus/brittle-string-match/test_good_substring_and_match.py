"""Near-misses: error messages and output matched by the part that matters.
Analysed, never run."""

import re

import pytest
from app import greet, validate

pytestmark = pytest.mark.unit


def test_invalid_email_mentions_the_at_sign():
    with pytest.raises(ValueError) as excinfo:
        validate("nope")
    assert "@" in str(excinfo.value)


def test_invalid_email_matches():
    with pytest.raises(ValueError, match=r"does not contain an @ symbol"):
        validate("nope")


def test_greeting_names_the_person(capsys):
    greet("Kenobi")
    assert "Hello there, general Kenobi" in capsys.readouterr().out


def test_greeting_matches_a_pattern(capsys):
    greet("Kenobi")
    assert re.search(r"Hello there, \w+", capsys.readouterr().out)
