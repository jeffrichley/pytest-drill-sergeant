"""Near-misses: expectations narrow enough to tell the right failure from a wrong
one, with or without `match=`. Analysed, never run."""

import pytest
from pytest import raises


def parse(text):
    return int(text)


class ParseException(Exception):
    pass


def strict_parse(text):
    raise ParseException(text)


def test_specific_type_without_match():
    with pytest.raises(ValueError):
        parse("x")


def test_specific_tuple_without_match():
    with pytest.raises((ValueError, TypeError)):
        parse(None)


def test_bare_name_with_a_specific_type():
    with raises(TypeError):
        parse(None)


def test_exception_subclass_named_like_it():
    with pytest.raises(ParseException):
        strict_parse("x")
