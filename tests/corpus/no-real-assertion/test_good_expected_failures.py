"""Near-misses: tests whose only assertion is an expected exception, warning or
failure. Analysed, never run."""

import warnings

import pytest
from pytest import raises


def parse(text):
    return int(text)


def test_bad_number_raises():
    with pytest.raises(ValueError, match="invalid literal"):
        parse("x")


def test_bad_number_raises_through_the_bare_name():
    with raises(ValueError, match="invalid literal"):
        parse("x")


def test_deprecation_warns():
    with pytest.warns(DeprecationWarning, match="old"):
        warnings.warn("old", DeprecationWarning, stacklevel=1)


def test_fails_loudly_on_an_unexpected_result():
    if parse("1") != 1:
        pytest.fail("parse broke")


def test_raises_assertion_error_on_mismatch():
    if parse("2") != 2:
        raise AssertionError("parse broke")


def test_assert_false_on_the_unreachable_branch():
    try:
        parse("x")
    except ValueError:
        return
    assert False, "parse accepted garbage"
