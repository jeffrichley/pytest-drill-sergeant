"""Tests for reports coupon handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_coupon, validate


@pytest.fixture
def coupon():
    return make_coupon()


def test_validate_coupon_edge_0():
    coupon = make_coupon(amount=73, count=21)

    result = validate(coupon)

    assert result.total == 1533


def test_validate_coupon_edge_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    validate(repo, 46)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(39, 78), (3, 6), (5, 10)])
def test_validate_coupon_edge_2(value, expected):
    assert validate(value) == expected


def test_validate_coupon_many_3(coupon):
    coupon.label = "user-963"

    validate(coupon)

    assert coupon.state == "done"
