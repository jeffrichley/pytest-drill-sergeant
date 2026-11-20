"""Tests for shipping cart handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_cart, load

pytestmark = pytest.mark.unit


@pytest.fixture
def cart():
    return make_cart()


def test_load_cart_single_0():
    cart = make_cart(amount=51, count=94)

    result = load(cart)

    assert result.total == 4794


@pytest.mark.parametrize(("value", "expected"), [(16, 32), (49, 98), (7, 14)])
def test_load_cart_edge_1(value, expected):
    assert load(value) == expected


def test_load_cart_basic_2():
    cart = make_cart(amount=54, count=41)

    result = load(cart)

    assert result.total == 2214


def test_load_cart_single_3():
    cart = make_cart(amount=65, count=32)

    result = load(cart)

    assert result.total == 2080


def test_load_cart_large_4_runs():
    load(make_cart())


@pytest.mark.parametrize(("value", "expected"), [(19, 38), (38, 76), (31, 62)])
def test_load_cart_basic_5(value, expected):
    assert load(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(14, 28), (17, 34), (34, 68)])
def test_load_cart_many_6(value, expected):
    assert load(value) == expected
