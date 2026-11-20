"""Tests for shipping coupon handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_coupon, parse


@pytest.fixture
def coupon():
    return make_coupon()


def test_parse_coupon_many_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    parse(repo, 474)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_coupon_many_1():
    coupon = make_coupon(amount=77, count=23)

    result = parse(coupon)

    assert result.total == 1771


def test_parse_coupon_large_2():
    coupon = make_coupon(amount=75, count=4)

    result = parse(coupon)

    assert result.total == 300


def test_parse_coupon_empty_3(coupon):
    coupon.label = "address-538"

    parse(coupon)

    assert coupon.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(48, 96), (41, 82), (47, 94)])
def test_parse_coupon_empty_4(value, expected):
    assert parse(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(3, 6), (43, 86), (8, 16)])
def test_parse_coupon_large_5(value, expected):
    assert parse(value) == expected
