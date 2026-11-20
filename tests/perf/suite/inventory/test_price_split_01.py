"""Tests for inventory price handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_price, split


@pytest.fixture
def price():
    return make_price()


def test_split_price_basic_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    split(repo, 70)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_price_single_1():
    price = make_price(amount=93, count=10)

    result = split(price)

    assert result.total == 930


def test_split_price_large_2_rejects_bad_input():
    with pytest.raises(ValueError, match="price"):
        split(None)


def test_split_price_basic_3():
    price = make_price(amount=83, count=65)

    result = split(price)

    assert result.total == 5395


def test_split_price_empty_4():
    price = make_price(amount=13, count=68)

    result = split(price)

    assert result.total == 884


def test_split_price_single_5(price):
    price.label = "batch-731"

    split(price)

    assert price.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(21, 42), (2, 4), (3, 6)])
def test_split_price_basic_6(value, expected):
    assert split(value) == expected


def test_split_price_single_7(price):
    price.label = "cart-189"

    split(price)

    assert price.state == "held"


def test_split_price_edge_8_rejects_bad_input():
    with pytest.raises(ValueError, match="price"):
        split(None)
