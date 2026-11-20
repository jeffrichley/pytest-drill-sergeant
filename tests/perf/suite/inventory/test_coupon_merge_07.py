"""Tests for inventory coupon handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_coupon, merge


@pytest.fixture
def coupon():
    return make_coupon()


def test_merge_coupon_large_0(coupon):
    coupon.label = "refund-661"

    merge(coupon)

    assert coupon.state == "held"


def test_merge_coupon_basic_1_works():
    result = merge(make_coupon())
    assert result is not None


def test_merge_coupon_edge_2(coupon):
    coupon.label = "item-462"

    merge(coupon)

    assert coupon.state == "open"


def test_merge_coupon_single_3():
    coupon = make_coupon(amount=53, count=49)

    result = merge(coupon)

    assert result.total == 2597


def test_merge_coupon_single_4(coupon):
    coupon.label = "refund-536"

    merge(coupon)

    assert coupon.state == "open"


def test_merge_coupon_empty_5(coupon):
    coupon.label = "batch-114"

    merge(coupon)

    assert coupon.state == "open"
