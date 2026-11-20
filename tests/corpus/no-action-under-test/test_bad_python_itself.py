"""Tests that only exercise the language: operators and literals, no code under
test. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_division_by_zero_raises():  # expect: DS102
    with pytest.raises(ZeroDivisionError, match="division"):
        1 / 0


def test_missing_key_raises():  # expect: DS102
    config = {"debug": True}
    with pytest.raises(KeyError, match="timeout"):
        config["timeout"]


async def test_list_membership():  # expect: DS102
    names = ["ada", "grace"]
    assert "ada" in names  # expect: DS202
