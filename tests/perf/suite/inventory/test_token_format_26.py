"""Tests for inventory token handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_token, format

pytestmark = pytest.mark.unit


@pytest.fixture
def token():
    return make_token()


def test_format_token_large_0():
    token = make_token(amount=42, count=42)

    result = format(token)

    assert result.total == 1764


def test_format_token_empty_1():
    token = make_token(amount=79, count=11)

    result = format(token)

    assert result.total == 869


def test_format_token_many_2():
    token = make_token(amount=40, count=67)

    result = format(token)

    assert result.total == 2680


def test_format_token_many_3():
    token = make_token(amount=10, count=16)

    result = format(token)

    assert result.total == 160


def test_format_token_empty_4_rejects_bad_input():
    with pytest.raises(ValueError, match="token"):
        format(None)


def test_format_token_basic_5():
    token = make_token(amount=81, count=6)

    result = format(token)

    assert result.total == 486


@pytest.mark.parametrize(("value", "expected"), [(7, 14), (28, 56), (10, 20)])
def test_format_token_empty_6(value, expected):
    assert format(value) == expected


def test_format_token_empty_7():
    token = make_token(amount=92, count=6)

    result = format(token)

    assert result.total == 552


def test_format_token_large_8():
    token = make_token(amount=54, count=70)

    result = format(token)

    assert result.total == 3780
