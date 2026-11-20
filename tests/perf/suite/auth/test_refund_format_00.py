"""Tests for auth refund handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_refund, format


@pytest.fixture
def refund():
    return make_refund()


def test_format_refund_single_0_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        format(None)


def test_format_refund_large_1():
    refund = make_refund(amount=64, count=23)

    result = format(refund)

    assert result.total == 1472


def test_format_refund_large_2():
    refund = make_refund(amount=8, count=23)

    result = format(refund)

    assert result.total == 184


@pytest.mark.parametrize(("value", "expected"), [(24, 48), (27, 54), (10, 20)])
def test_format_refund_single_3(value, expected):
    assert format(value) == expected
