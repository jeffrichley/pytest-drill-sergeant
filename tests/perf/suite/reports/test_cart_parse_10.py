"""Tests for reports cart handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_cart, parse

pytestmark = pytest.mark.unit


@pytest.fixture
def cart():
    return make_cart()


def test_parse_cart_empty_0():
    cart = make_cart(amount=80, count=82)

    result = parse(cart)

    assert result.total == 6560


def test_parse_cart_empty_1():
    cart = make_cart(amount=9, count=7)

    result = parse(cart)

    assert result.total == 63


def test_parse_cart_many_2_runs():
    parse(make_cart())


def test_parse_cart_edge_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    parse(repo, 105)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(40, 80), (8, 16), (6, 12)])
def test_parse_cart_single_4(value, expected):
    assert parse(value) == expected


def test_parse_cart_single_5():
    cart = make_cart(amount=81, count=32)

    result = parse(cart)

    assert result.total == 2592


def test_parse_cart_basic_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    parse(repo, 95)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_cart_empty_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    parse(repo, 435)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
