"""Tests that build the expected value and the "actual" value the same way, with
nothing run in between. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


class TestUser:
    def test_default_name(self):  # expect: DS102
        user = {"name": "Ada"}
        assert user["name"] == "Ada"

    def test_flags(self):  # expect: DS102
        flags = ("a", "b")
        assert flags[0] == "a"


def test_mirror():  # expect: DS102
    actual = [1, 2, 3]
    expected = [1, 2, 3]
    assert actual == expected  # expect: DS202
