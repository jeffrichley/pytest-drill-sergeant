"""Tests for reports coupon handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_coupon, format

pytestmark = pytest.mark.unit


@pytest.fixture
def coupon():
    return make_coupon()


@pytest.mark.parametrize(("value", "expected"), [(20, 40), (43, 86), (6, 12)])
def test_format_coupon_single_0(value, expected):
    assert format(value) == expected


def test_format_coupon_many_1_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        format(None)


def test_format_coupon_many_2():
    coupon = make_coupon(amount=77, count=55)

    result = format(coupon)

    assert result.total == 4235


def test_format_coupon_single_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    format(repo, 297)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
