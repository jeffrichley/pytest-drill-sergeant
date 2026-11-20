"""Tests for reports coupon handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_coupon, validate

pytestmark = pytest.mark.unit


@pytest.fixture
def coupon():
    return make_coupon()


def test_validate_coupon_single_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    validate(repo, 93)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_coupon_many_1_works():
    result = validate(make_coupon())
    assert result is not None


def test_validate_coupon_many_2(coupon):
    coupon.label = "token-227"

    validate(coupon)

    assert coupon.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(7, 14), (20, 40), (37, 74)])
def test_validate_coupon_basic_3(value, expected):
    assert validate(value) == expected


def test_validate_coupon_empty_4(coupon):
    coupon.label = "refund-518"

    validate(coupon)

    assert coupon.state == "open"


def test_validate_coupon_edge_5():
    coupon = make_coupon(amount=41, count=8)

    result = validate(coupon)

    assert result.total == 328


def test_validate_coupon_many_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    validate(repo, 113)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
