"""Tests for orders coupon handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_coupon, merge


@pytest.fixture
def coupon():
    return make_coupon()


def test_merge_coupon_single_0(coupon):
    coupon.label = "batch-271"

    merge(coupon)

    assert coupon.state == "held"


def test_merge_coupon_basic_1():
    coupon = make_coupon(amount=26, count=21)

    result = merge(coupon)

    assert result.total == 546


def test_merge_coupon_basic_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    merge(repo, 89)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_coupon_edge_3():
    coupon = make_coupon(amount=15, count=25)

    result = merge(coupon)

    assert result.total == 375


def test_merge_coupon_empty_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    merge(repo, 459)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_coupon_basic_5_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        merge(None)


def test_merge_coupon_basic_6():
    coupon = make_coupon(amount=25, count=38)

    result = merge(coupon)

    assert result.total == 950
