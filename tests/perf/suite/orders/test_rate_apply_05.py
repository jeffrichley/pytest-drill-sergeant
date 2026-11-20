"""Tests for orders rate handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_rate, apply

pytestmark = pytest.mark.unit


@pytest.fixture
def rate():
    return make_rate()


def test_apply_rate_basic_0():
    rate = make_rate(amount=9, count=63)

    result = apply(rate)

    assert result.total == 567


@pytest.mark.parametrize(("value", "expected"), [(12, 24), (29, 58), (3, 6)])
def test_apply_rate_basic_1(value, expected):
    assert apply(value) == expected


def test_apply_rate_many_2(rate):
    rate.label = "session-357"

    apply(rate)

    assert rate.state == "done"


def test_apply_rate_basic_3():
    rate = make_rate(amount=24, count=25)

    result = apply(rate)

    assert result.total == 600


def test_apply_rate_basic_4_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        apply(None)


def test_apply_rate_many_5(rate):
    rate.label = "batch-343"

    apply(rate)

    assert rate.state == "open"
