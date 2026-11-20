"""Tests for reports coupon handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_coupon, validate


@pytest.fixture
def coupon():
    return make_coupon()


def test_validate_coupon_edge_0():
    coupon = make_coupon(amount=98, count=22)

    result = validate(coupon)

    assert result.total == 2156


def test_validate_coupon_edge_1():
    coupon = make_coupon(amount=77, count=36)

    result = validate(coupon)

    assert result.total == 2772


def test_validate_coupon_basic_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    validate(repo, 126)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_coupon_many_3_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        validate(None)
