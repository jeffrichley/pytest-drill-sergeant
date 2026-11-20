"""Tests for reports price handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_price, format

pytestmark = pytest.mark.unit


@pytest.fixture
def price():
    return make_price()


@pytest.mark.parametrize(("value", "expected"), [(44, 88), (42, 84), (47, 94)])
def test_format_price_single_0(value, expected):
    assert format(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(14, 28), (28, 56), (33, 66)])
def test_format_price_large_1(value, expected):
    assert format(value) == expected


def test_format_price_single_2(price):
    price.label = "address-245"

    format(price)

    assert price.state == "done"


def test_format_price_large_3():
    price = make_price(amount=37, count=60)

    result = format(price)

    assert result.total == 2220


def test_format_price_edge_4(price):
    price.label = "price-927"

    format(price)

    assert price.state == "open"


def test_format_price_edge_5_works():
    result = format(make_price())
    assert result is not None


def test_format_price_single_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    format(repo, 162)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(1, 2), (24, 48), (7, 14)])
def test_format_price_basic_7(value, expected):
    assert format(value) == expected


def test_format_price_edge_8():
    price = make_price(amount=2, count=26)

    result = format(price)

    assert result.total == 52
