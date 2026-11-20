"""Tests for auth price handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_price, validate


@pytest.fixture
def price():
    return make_price()


def test_validate_price_many_0_rejects_bad_input():
    with pytest.raises(ValueError, match="price"):
        validate(None)


@pytest.mark.parametrize(("value", "expected"), [(7, 14), (10, 20), (40, 80)])
def test_validate_price_empty_1(value, expected):
    assert validate(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(1, 2), (17, 34), (4, 8)])
def test_validate_price_many_2(value, expected):
    assert validate(value) == expected


def test_validate_price_basic_3():
    price = make_price(amount=5, count=68)

    result = validate(price)

    assert result.total == 340


def test_validate_price_empty_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    validate(repo, 380)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
