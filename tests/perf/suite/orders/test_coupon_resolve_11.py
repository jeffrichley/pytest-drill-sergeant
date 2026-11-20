"""Tests for orders coupon handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_coupon, resolve


@pytest.fixture
def coupon():
    return make_coupon()


def test_resolve_coupon_single_0(coupon):
    coupon.label = "token-488"

    resolve(coupon)

    assert coupon.state == "open"


def test_resolve_coupon_basic_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    resolve(repo, 196)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_coupon_basic_2(coupon):
    coupon.label = "report-303"

    resolve(coupon)

    assert coupon.state == "held"


def test_resolve_coupon_empty_3():
    coupon = make_coupon(amount=12, count=22)

    result = resolve(coupon)

    assert result.total == 264


def test_resolve_coupon_edge_4_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        resolve(None)
