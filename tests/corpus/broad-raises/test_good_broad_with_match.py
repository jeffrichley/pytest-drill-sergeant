"""Near-misses: a broad type pinned down by `match=`. Analysed, never run."""

import pytest


def parse(text):
    return int(text)


def test_broad_type_with_a_match():
    with pytest.raises(Exception, match="invalid literal"):
        parse("x")


def test_base_exception_with_a_match():
    with pytest.raises(BaseException, match="int()"):
        parse(None)


def test_function_form_with_a_match():
    pytest.raises(Exception, parse, "x", match="invalid literal")


def test_broad_tuple_with_a_match():
    with pytest.raises((ValueError, Exception), match="invalid"):
        parse("x")


def test_broad_type_matched_afterwards():
    with pytest.raises(Exception) as excinfo:
        parse("x")
    excinfo.match("invalid literal")
