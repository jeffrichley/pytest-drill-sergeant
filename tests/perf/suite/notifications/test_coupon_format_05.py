"""Tests for notifications coupon handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_coupon, format


@pytest.fixture
def coupon():
    return make_coupon()


@pytest.mark.parametrize(("value", "expected"), [(42, 84), (2, 4), (28, 56)])
def test_format_coupon_large_0(value, expected):
    assert format(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(43, 86), (44, 88), (20, 40)])
def test_format_coupon_basic_1(value, expected):
    assert format(value) == expected


def test_format_coupon_single_2():
    coupon = make_coupon(amount=16, count=74)

    result = format(coupon)

    assert result.total == 1184


def test_format_coupon_many_3():
    coupon = make_coupon(amount=13, count=21)

    result = format(coupon)

    assert result.total == 273


@pytest.mark.parametrize(("value", "expected"), [(19, 38), (2, 4), (17, 34)])
def test_format_coupon_large_4(value, expected):
    assert format(value) == expected


def test_format_coupon_large_5(coupon):
    coupon.label = "batch-673"

    format(coupon)

    assert coupon.state == "held"
