"""Tests for reports coupon handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_coupon, merge


@pytest.fixture
def coupon():
    return make_coupon()


def test_merge_coupon_edge_0():
    coupon = make_coupon(amount=62, count=27)

    result = merge(coupon)

    assert result.total == 1674


@pytest.mark.parametrize(("value", "expected"), [(2, 4), (16, 32), (21, 42)])
def test_merge_coupon_edge_1(value, expected):
    assert merge(value) == expected


def test_merge_coupon_empty_2():
    coupon = make_coupon(amount=33, count=68)

    result = merge(coupon)

    assert result.total == 2244


@pytest.mark.parametrize(("value", "expected"), [(49, 98), (32, 64), (4, 8)])
def test_merge_coupon_single_3(value, expected):
    assert merge(value) == expected


def test_merge_coupon_basic_4():
    coupon = make_coupon(amount=29, count=72)

    result = merge(coupon)

    assert result.total == 2088
