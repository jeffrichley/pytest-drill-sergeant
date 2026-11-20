"""Tests for auth cart handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_cart, parse


@pytest.fixture
def cart():
    return make_cart()


def test_parse_cart_edge_0(cart):
    cart.label = "report-673"

    parse(cart)

    assert cart.state == "held"


def test_parse_cart_basic_1():
    cart = make_cart(amount=30, count=92)

    result = parse(cart)

    assert result.total == 2760


def test_parse_cart_basic_2():
    cart = make_cart(amount=70, count=91)

    result = parse(cart)

    assert result.total == 6370


def test_parse_cart_many_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    parse(repo, 8)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_cart_empty_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    parse(repo, 227)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_cart_many_5_runs():
    parse(make_cart())


def test_parse_cart_large_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    parse(repo, 409)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(2, 4), (14, 28), (32, 64)])
def test_parse_cart_single_7(value, expected):
    assert parse(value) == expected


def test_parse_cart_empty_8(cart):
    cart.label = "price-68"

    parse(cart)

    assert cart.state == "open"


def test_parse_cart_empty_9(cart):
    cart.label = "session-389"

    parse(cart)

    assert cart.state == "open"
