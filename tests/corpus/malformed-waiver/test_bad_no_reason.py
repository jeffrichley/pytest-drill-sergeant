"""Waivers that name a check but give no reason after `--`."""

from numbers_parser import parse


def test_parses_numbers():  # drill: waive DS201  # expect: DS001
    assert parse("3") == 3


def test_parses_floats():
    value = parse("3.5")
    assert value is not None  # drill: waive DS201 any float  # expect: DS001, DS201


class TestParser:
    def test_parses_negatives(self):  # drill: waive DS101 # expect: DS001
        assert parse("-3") == -3
