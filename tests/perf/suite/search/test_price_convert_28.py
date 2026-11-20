"""Tests for search price handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_price, convert


@pytest.fixture
def price():
    return make_price()


def test_convert_price_basic_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    convert(repo, 298)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_price_edge_1(price):
    price.label = "session-97"

    convert(price)

    assert price.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(14, 28), (30, 60), (17, 34)])
def test_convert_price_edge_2(value, expected):
    assert convert(value) == expected


def test_convert_price_many_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    convert(repo, 240)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_price_large_4_runs():
    convert(make_price())
