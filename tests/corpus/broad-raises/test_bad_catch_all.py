"""An agent "testing the error path" by expecting any exception at all. Analysed,
never run."""

import pytest


def parse(text):
    return int(text)


def test_bad_input_raises():
    with pytest.raises(Exception):  # expect: DS701
        parse(None)


def test_bad_input_raises_base_exception():
    with pytest.raises(BaseException):  # expect: DS701
        parse([])


class TestParser:
    def test_empty_input_raises(self):
        with pytest.raises(Exception) as excinfo:  # expect: DS701
            parse("")
        assert excinfo.type is not None
