"""Tests for inventory coupon handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_coupon, apply


@pytest.fixture
def coupon():
    return make_coupon()


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (34, 68), (42, 84)])
def test_apply_coupon_many_0(value, expected):
    assert apply(value) == expected


def test_apply_coupon_large_1(coupon):
    coupon.label = "price-11"

    apply(coupon)

    assert coupon.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(49, 98), (34, 68), (44, 88)])
def test_apply_coupon_large_2(value, expected):
    assert apply(value) == expected


def test_apply_coupon_empty_3():
    coupon = make_coupon(amount=15, count=58)

    result = apply(coupon)

    assert result.total == 870


@pytest.mark.parametrize(("value", "expected"), [(44, 88), (5, 10), (26, 52)])
def test_apply_coupon_large_4(value, expected):
    assert apply(value) == expected


def test_apply_coupon_empty_5(coupon):
    coupon.label = "report-291"

    apply(coupon)

    assert coupon.state == "held"


def test_apply_coupon_large_6():
    coupon = make_coupon(amount=79, count=17)

    result = apply(coupon)

    assert result.total == 1343


@pytest.mark.parametrize(("value", "expected"), [(28, 56), (7, 14), (18, 36)])
def test_apply_coupon_many_7(value, expected):
    assert apply(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(28, 56), (45, 90), (4, 8)])
def test_apply_coupon_large_8(value, expected):
    assert apply(value) == expected
