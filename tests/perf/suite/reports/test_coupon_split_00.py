"""Tests for reports coupon handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_coupon, split


@pytest.fixture
def coupon():
    return make_coupon()


def test_split_coupon_single_0():
    coupon = make_coupon(amount=94, count=9)

    result = split(coupon)

    assert result.total == 846


def test_split_coupon_edge_1(coupon):
    coupon.label = "address-326"

    split(coupon)

    assert coupon.state == "open"


def test_split_coupon_single_2(coupon):
    coupon.label = "refund-284"

    split(coupon)

    assert coupon.state == "open"


def test_split_coupon_basic_3():
    coupon = make_coupon(amount=16, count=92)

    result = split(coupon)

    assert result.total == 1472


def test_split_coupon_single_4(coupon):
    coupon.label = "cart-504"

    split(coupon)

    assert coupon.state == "done"


def test_split_coupon_single_5():
    coupon = make_coupon(amount=3, count=5)

    result = split(coupon)

    assert result.total == 15
