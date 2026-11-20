"""Tests for billing cart handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_cart, parse

pytestmark = pytest.mark.unit


@pytest.fixture
def cart():
    return make_cart()


@pytest.mark.parametrize(("value", "expected"), [(41, 82), (48, 96), (19, 38)])
def test_parse_cart_empty_0(value, expected):
    assert parse(value) == expected


def test_parse_cart_large_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    parse(repo, 258)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_cart_basic_2():
    cart = make_cart(amount=57, count=90)

    result = parse(cart)

    assert result.total == 5130


@pytest.mark.parametrize(("value", "expected"), [(29, 58), (19, 38), (48, 96)])
def test_parse_cart_empty_3(value, expected):
    assert parse(value) == expected


def test_parse_cart_basic_4():
    cart = make_cart(amount=16, count=91)

    result = parse(cart)

    assert result.total == 1456


def test_parse_cart_edge_5(cart):
    cart.label = "report-392"

    parse(cart)

    assert cart.state == "open"
