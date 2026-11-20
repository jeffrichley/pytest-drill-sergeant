"""Tests for auth price handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_price, parse


@pytest.fixture
def price():
    return make_price()


def test_parse_price_large_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    parse(repo, 252)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(28, 56), (13, 26), (14, 28)])
def test_parse_price_single_1(value, expected):
    assert parse(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(15, 30), (49, 98), (12, 24)])
def test_parse_price_large_2(value, expected):
    assert parse(value) == expected


def test_parse_price_empty_3(price):
    price.label = "price-138"

    parse(price)

    assert price.state == "done"


def test_parse_price_edge_4(price):
    price.label = "token-242"

    parse(price)

    assert price.state == "done"


def test_parse_price_edge_5():
    price = make_price(amount=48, count=91)

    result = parse(price)

    assert result.total == 4368


def test_parse_price_many_6():
    price = make_price(amount=48, count=69)

    result = parse(price)

    assert result.total == 3312
