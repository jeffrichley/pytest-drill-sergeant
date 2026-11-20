"""Tests for billing coupon handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_coupon, validate

pytestmark = pytest.mark.unit


@pytest.fixture
def coupon():
    return make_coupon()


def test_validate_coupon_empty_0_runs():
    validate(make_coupon())


def test_validate_coupon_empty_1():
    coupon = make_coupon(amount=34, count=72)

    result = validate(coupon)

    assert result.total == 2448


def test_validate_coupon_empty_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    validate(repo, 370)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_coupon_empty_3():
    coupon = make_coupon(amount=36, count=27)

    result = validate(coupon)

    assert result.total == 972


def test_validate_coupon_empty_4():
    coupon = make_coupon(amount=1, count=82)

    result = validate(coupon)

    assert result.total == 82


def test_validate_coupon_many_5_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        validate(None)
