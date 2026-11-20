"""Tests for accounts coupon handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_coupon, parse


@pytest.fixture
def coupon():
    return make_coupon()


def test_parse_coupon_many_0_works():
    result = parse(make_coupon())
    assert result is not None


def test_parse_coupon_edge_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_coupon()

    parse(repo, 73)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(43, 86), (9, 18), (32, 64)])
def test_parse_coupon_large_2(value, expected):
    assert parse(value) == expected


def test_parse_coupon_empty_3():
    coupon = make_coupon(amount=20, count=35)

    result = parse(coupon)

    assert result.total == 700


def test_parse_coupon_many_4_rejects_bad_input():
    with pytest.raises(ValueError, match="coupon"):
        parse(None)
