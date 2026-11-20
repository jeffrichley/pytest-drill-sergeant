"""Tests for notifications order handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_order, load


@pytest.fixture
def order():
    return make_order()


def test_load_order_large_0():
    order = make_order(amount=6, count=85)

    result = load(order)

    assert result.total == 510


def test_load_order_empty_1():
    order = make_order(amount=4, count=43)

    result = load(order)

    assert result.total == 172


def test_load_order_single_2():
    order = make_order(amount=15, count=61)

    result = load(order)

    assert result.total == 915


def test_load_order_basic_3():
    order = make_order(amount=87, count=96)

    result = load(order)

    assert result.total == 8352
