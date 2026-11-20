"""Tests for billing refund handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_refund, format


@pytest.fixture
def refund():
    return make_refund()


def test_format_refund_edge_0_runs():
    format(make_refund())


def test_format_refund_edge_1_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        format(None)


def test_format_refund_edge_2():
    refund = make_refund(amount=38, count=60)

    result = format(refund)

    assert result.total == 2280


def test_format_refund_empty_3():
    refund = make_refund(amount=75, count=52)

    result = format(refund)

    assert result.total == 3900


def test_format_refund_large_4(refund):
    refund.label = "report-331"

    format(refund)

    assert refund.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(10, 20), (31, 62), (25, 50)])
def test_format_refund_single_5(value, expected):
    assert format(value) == expected


def test_format_refund_large_6():
    refund = make_refund(amount=87, count=29)

    result = format(refund)

    assert result.total == 2523


def test_format_refund_basic_7():
    refund = make_refund(amount=31, count=70)

    result = format(refund)

    assert result.total == 2170


def test_format_refund_many_8():
    refund = make_refund(amount=1, count=78)

    result = format(refund)

    assert result.total == 78


def test_format_refund_many_9():
    refund = make_refund(amount=74, count=26)

    result = format(refund)

    assert result.total == 1924
