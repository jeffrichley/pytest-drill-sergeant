"""Tests for reports coupon handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_coupon, merge

pytestmark = pytest.mark.unit


@pytest.fixture
def coupon():
    return make_coupon()


def test_merge_coupon_basic_0():
    coupon = make_coupon(amount=57, count=5)

    result = merge(coupon)

    assert result.total == 285


def test_merge_coupon_edge_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    merge(repo, 380)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_coupon_empty_2(coupon):
    coupon.label = "item-771"

    merge(coupon)

    assert coupon.state == "held"


def test_merge_coupon_edge_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    merge(repo, 227)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_coupon_empty_4():
    coupon = make_coupon(amount=97, count=20)

    result = merge(coupon)

    assert result.total == 1940


def test_merge_coupon_edge_5():
    coupon = make_coupon(amount=96, count=46)

    result = merge(coupon)

    assert result.total == 4416


def test_merge_coupon_many_6():
    coupon = make_coupon(amount=76, count=8)

    result = merge(coupon)

    assert result.total == 608
