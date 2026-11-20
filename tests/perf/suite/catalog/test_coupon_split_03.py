"""Tests for catalog coupon handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_coupon, split


@pytest.fixture
def coupon():
    return make_coupon()


def test_split_coupon_many_0_runs():
    split(make_coupon())


def test_split_coupon_basic_1():
    coupon = make_coupon(amount=78, count=38)

    result = split(coupon)

    assert result.total == 2964


def test_split_coupon_edge_2():
    coupon = make_coupon(amount=6, count=93)

    result = split(coupon)

    assert result.total == 558


def test_split_coupon_empty_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    split(repo, 433)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_coupon_large_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    split(repo, 349)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_coupon_large_5(coupon):
    coupon.label = "invoice-479"

    split(coupon)

    assert coupon.state == "held"


def test_split_coupon_basic_6():
    coupon = make_coupon(amount=59, count=93)

    result = split(coupon)

    assert result.total == 5487


def test_split_coupon_large_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    split(repo, 454)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_coupon_basic_8():
    coupon = make_coupon(amount=3, count=62)

    result = split(coupon)

    assert result.total == 186
