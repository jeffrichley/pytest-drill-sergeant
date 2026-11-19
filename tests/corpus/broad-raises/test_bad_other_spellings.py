"""A broad expectation spelled every other way pytest accepts it. Analysed, never
run."""

import pytest
from pytest import raises


def parse(text):
    return int(text)


def test_bare_name_raises():
    with raises(Exception):  # expect: DS701
        parse(None)


def test_tuple_with_a_broad_member():
    with pytest.raises((ValueError, Exception)):  # expect: DS701
        parse(None)


def test_function_form():
    pytest.raises(Exception, parse, None)  # expect: DS701


def test_keyword_form():
    with pytest.raises(expected_exception=BaseException):  # expect: DS701
        parse(None)


def test_match_none_is_no_match():
    with pytest.raises(Exception, match=None):  # expect: DS701
        parse(None)
