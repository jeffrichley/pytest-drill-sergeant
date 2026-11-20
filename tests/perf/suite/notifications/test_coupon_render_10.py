"""Tests for notifications coupon handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_coupon, render

pytestmark = pytest.mark.unit


@pytest.fixture
def coupon():
    return make_coupon()


def test_render_coupon_many_0(coupon):
    coupon.label = "order-766"

    render(coupon)

    assert coupon.state == "open"


def test_render_coupon_basic_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    render(repo, 153)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(17, 34), (27, 54), (30, 60)])
def test_render_coupon_large_2(value, expected):
    assert render(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(45, 90), (17, 34), (47, 94)])
def test_render_coupon_edge_3(value, expected):
    assert render(value) == expected


def test_render_coupon_large_4():
    coupon = make_coupon(amount=67, count=48)

    result = render(coupon)

    assert result.total == 3216


def test_render_coupon_basic_5_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        render(None)


def test_render_coupon_many_6_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        render(None)
