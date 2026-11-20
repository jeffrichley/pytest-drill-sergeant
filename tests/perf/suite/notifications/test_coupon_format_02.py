"""Tests for notifications coupon handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_coupon, format


@pytest.fixture
def coupon():
    return make_coupon()


def test_format_coupon_large_0():
    coupon = make_coupon(amount=28, count=13)

    result = format(coupon)

    assert result.total == 364


def test_format_coupon_basic_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    format(repo, 298)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_format_coupon_empty_2():
    coupon = make_coupon(amount=52, count=11)

    result = format(coupon)

    assert result.total == 572


def test_format_coupon_many_3():
    coupon = make_coupon(amount=60, count=83)

    result = format(coupon)

    assert result.total == 4980


def test_format_coupon_empty_4_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        format(None)


@pytest.mark.parametrize(("value", "expected"), [(11, 22), (33, 66), (32, 64)])
def test_format_coupon_empty_5(value, expected):
    assert format(value) == expected
