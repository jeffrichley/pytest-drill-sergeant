"""Tests for reports coupon handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_coupon, format


@pytest.fixture
def coupon():
    return make_coupon()


def test_format_coupon_empty_0(coupon):
    coupon.label = "event-105"

    format(coupon)

    assert coupon.state == "done"


def test_format_coupon_empty_1_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        format(None)


def test_format_coupon_empty_2(coupon):
    coupon.label = "refund-397"

    format(coupon)

    assert coupon.state == "done"


def test_format_coupon_edge_3(coupon):
    coupon.label = "price-275"

    format(coupon)

    assert coupon.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(17, 34), (25, 50), (31, 62)])
def test_format_coupon_single_4(value, expected):
    assert format(value) == expected


def test_format_coupon_edge_5():
    coupon = make_coupon(amount=99, count=72)

    result = format(coupon)

    assert result.total == 7128


def test_format_coupon_many_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    format(repo, 402)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_format_coupon_edge_7():
    coupon = make_coupon(amount=50, count=89)

    result = format(coupon)

    assert result.total == 4450


def test_format_coupon_edge_8_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        format(None)
