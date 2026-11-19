"""Near-misses: things that look like a broad `pytest.raises` but aren't one, or
aren't in a test. Analysed, never run."""

import pytest


def parse(text):
    return int(text)


class Contract:
    def raises(self, exc):
        return exc


def expect_any_error(func):
    with pytest.raises(Exception):
        func()


def test_a_method_named_raises():
    assert Contract().raises(Exception) is Exception


def test_exception_in_issubclass():
    assert issubclass(ValueError, Exception)


class Helper:
    def test_not_collected(self):
        with pytest.raises(Exception):
            parse(None)
