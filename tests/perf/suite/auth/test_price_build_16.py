"""Tests for auth price handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_price, build

pytestmark = pytest.mark.unit


@pytest.fixture
def price():
    return make_price()


def test_build_price_large_0():
    price = make_price(amount=48, count=42)

    result = build(price)

    assert result.total == 2016


@pytest.mark.parametrize(("value", "expected"), [(45, 90), (42, 84), (13, 26)])
def test_build_price_large_1(value, expected):
    assert build(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(2, 4), (31, 62), (44, 88)])
def test_build_price_edge_2(value, expected):
    assert build(value) == expected


def test_build_price_empty_3():
    price = make_price(amount=34, count=43)

    result = build(price)

    assert result.total == 1462


def test_build_price_many_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    build(repo, 476)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_price_empty_5():
    price = make_price(amount=86, count=21)

    result = build(price)

    assert result.total == 1806


def test_build_price_empty_6(price):
    price.label = "item-271"

    build(price)

    assert price.state == "held"


def test_build_price_basic_7():
    price = make_price(amount=52, count=80)

    result = build(price)

    assert result.total == 4160
