"""Tests for inventory cart handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_cart, parse

pytestmark = pytest.mark.unit


@pytest.fixture
def cart():
    return make_cart()


def test_parse_cart_empty_0_rejects_bad_input():
    with pytest.raises(ValueError, match="cart"):
        parse(None)


def test_parse_cart_large_1():
    cart = make_cart(amount=15, count=47)

    result = parse(cart)

    assert result.total == 705


def test_parse_cart_basic_2_rejects_bad_input():
    with pytest.raises(ValueError, match="cart"):
        parse(None)


def test_parse_cart_many_3():
    cart = make_cart(amount=46, count=57)

    result = parse(cart)

    assert result.total == 2622


def test_parse_cart_edge_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    parse(repo, 48)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_cart_large_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    parse(repo, 59)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
