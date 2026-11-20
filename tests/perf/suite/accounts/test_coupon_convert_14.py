"""Tests for accounts coupon handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_coupon, convert

pytestmark = pytest.mark.unit


@pytest.fixture
def coupon():
    return make_coupon()


def test_convert_coupon_large_0_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        convert(None)


def test_convert_coupon_large_1():
    coupon = make_coupon(amount=53, count=13)

    result = convert(coupon)

    assert result.total == 689


def test_convert_coupon_empty_2():
    coupon = make_coupon(amount=41, count=66)

    result = convert(coupon)

    assert result.total == 2706


def test_convert_coupon_basic_3():
    coupon = make_coupon(amount=82, count=44)

    result = convert(coupon)

    assert result.total == 3608


def test_convert_coupon_empty_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    convert(repo, 307)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_coupon_many_5(coupon):
    coupon.label = "coupon-949"

    convert(coupon)

    assert coupon.state == "held"


def test_convert_coupon_empty_6():
    coupon = make_coupon(amount=30, count=16)

    result = convert(coupon)

    assert result.total == 480


@pytest.mark.parametrize(("value", "expected"), [(16, 32), (47, 94), (28, 56)])
def test_convert_coupon_large_7(value, expected):
    assert convert(value) == expected
