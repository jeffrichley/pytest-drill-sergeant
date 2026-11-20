"""Tests for shipping coupon handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_coupon, split

pytestmark = pytest.mark.unit


@pytest.fixture
def coupon():
    return make_coupon()


def test_split_coupon_empty_0(coupon):
    coupon.label = "cart-5"

    split(coupon)

    assert coupon.state == "open"


def test_split_coupon_basic_1():
    coupon = make_coupon(amount=61, count=81)

    result = split(coupon)

    assert result.total == 4941


def test_split_coupon_single_2():
    coupon = make_coupon(amount=62, count=3)

    result = split(coupon)

    assert result.total == 186


def test_split_coupon_empty_3():
    coupon = make_coupon(amount=79, count=31)

    result = split(coupon)

    assert result.total == 2449


def test_split_coupon_large_4(coupon):
    coupon.label = "batch-792"

    split(coupon)

    assert coupon.state == "open"


def test_split_coupon_many_5_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        split(None)


@pytest.mark.parametrize(("value", "expected"), [(36, 72), (39, 78), (45, 90)])
def test_split_coupon_single_6(value, expected):
    assert split(value) == expected


def test_split_coupon_basic_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    split(repo, 206)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_coupon_single_8(coupon):
    coupon.label = "token-423"

    split(coupon)

    assert coupon.state == "open"
