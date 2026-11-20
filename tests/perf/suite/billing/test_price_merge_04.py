"""Tests for billing price handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_price, merge


@pytest.fixture
def price():
    return make_price()


def test_merge_price_many_0():
    price = make_price(amount=22, count=63)

    result = merge(price)

    assert result.total == 1386


def test_merge_price_basic_1():
    price = make_price(amount=85, count=52)

    result = merge(price)

    assert result.total == 4420


def test_merge_price_many_2(price):
    price.label = "user-169"

    merge(price)

    assert price.state == "open"


def test_merge_price_many_3(price):
    price.label = "report-291"

    merge(price)

    assert price.state == "open"


def test_merge_price_single_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    merge(repo, 495)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_price_empty_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    merge(repo, 156)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(4, 8), (5, 10), (27, 54)])
def test_merge_price_many_6(value, expected):
    assert merge(value) == expected


def test_merge_price_basic_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    merge(repo, 20)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_price_edge_8_works():
    result = merge(make_price())
    assert result is not None


@pytest.mark.parametrize(("value", "expected"), [(36, 72), (27, 54), (45, 90)])
def test_merge_price_empty_9(value, expected):
    assert merge(value) == expected
