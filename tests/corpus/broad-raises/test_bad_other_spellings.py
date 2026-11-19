"""A broad expectation spelled every other way pytest accepts it. Analysed, never
run."""

import pytest
import pytest as pt
from pytest import raises
from pytest import raises as expect


def parse(text):
    return int(text)


def test_bare_name_raises():
    with raises(Exception):  # expect: DS701
        parse(None)


def test_tuple_with_a_broad_member():
    with pytest.raises((ValueError, Exception)):  # expect: DS701
        parse(None)


def test_keyword_form():
    with pytest.raises(expected_exception=BaseException):  # expect: DS701
        parse(None)


def test_match_none_is_no_match():
    with pytest.raises(Exception, match=None):  # expect: DS701
        parse(None)


def test_empty_match_matches_everything():
    with pytest.raises(Exception, match=""):  # expect: DS701
        parse(None)


def test_aliased_module():
    with pt.raises(Exception):  # expect: DS701
        parse(None)


def test_aliased_name():
    with expect(BaseException):  # expect: DS701
        parse(None)
