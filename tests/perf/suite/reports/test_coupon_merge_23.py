"""Tests for reports coupon handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_coupon, merge


@pytest.fixture
def coupon():
    return make_coupon()


def test_merge_coupon_many_0(coupon):
    coupon.label = "price-841"

    merge(coupon)

    assert coupon.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(37, 74), (10, 20), (9, 18)])
def test_merge_coupon_single_1(value, expected):
    assert merge(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(5, 10), (31, 62), (7, 14)])
def test_merge_coupon_single_2(value, expected):
    assert merge(value) == expected


def test_merge_coupon_single_3_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        merge(None)


@pytest.mark.parametrize(("value", "expected"), [(38, 76), (11, 22), (40, 80)])
def test_merge_coupon_many_4(value, expected):
    assert merge(value) == expected


def test_merge_coupon_large_5():
    coupon = make_coupon(amount=64, count=84)

    result = merge(coupon)

    assert result.total == 5376


def test_merge_coupon_edge_6_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        merge(None)


def test_merge_coupon_edge_7_runs():
    merge(make_coupon())
