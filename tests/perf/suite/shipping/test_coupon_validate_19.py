"""Tests for shipping coupon handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_coupon, validate


@pytest.fixture
def coupon():
    return make_coupon()


@pytest.mark.parametrize(("value", "expected"), [(40, 80), (22, 44), (34, 68)])
def test_validate_coupon_single_0(value, expected):
    assert validate(value) == expected


def test_validate_coupon_edge_1_works():
    result = validate(make_coupon())
    assert result is not None


def test_validate_coupon_single_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    validate(repo, 366)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(37, 74), (24, 48), (36, 72)])
def test_validate_coupon_basic_3(value, expected):
    assert validate(value) == expected


def test_validate_coupon_many_4(coupon):
    coupon.label = "refund-118"

    validate(coupon)

    assert coupon.state == "held"


def test_validate_coupon_many_5():
    coupon = make_coupon(amount=59, count=68)

    result = validate(coupon)

    assert result.total == 4012
