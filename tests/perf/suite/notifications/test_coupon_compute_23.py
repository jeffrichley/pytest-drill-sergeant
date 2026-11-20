"""Tests for notifications coupon handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_coupon, compute

pytestmark = pytest.mark.unit


@pytest.fixture
def coupon():
    return make_coupon()


def test_compute_coupon_single_0():
    coupon = make_coupon(amount=25, count=60)

    result = compute(coupon)

    assert result.total == 1500


def test_compute_coupon_large_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    compute(repo, 99)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_coupon_basic_2(coupon):
    coupon.label = "cart-769"

    compute(coupon)

    assert coupon.state == "done"


def test_compute_coupon_basic_3(coupon):
    coupon.label = "report-820"

    compute(coupon)

    assert coupon.state == "held"
