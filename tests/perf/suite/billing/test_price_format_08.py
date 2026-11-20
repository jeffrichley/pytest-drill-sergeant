"""Tests for billing price handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_price, format


@pytest.fixture
def price():
    return make_price()


def test_format_price_basic_0(price):
    price.label = "invoice-60"

    format(price)

    assert price.state == "open"


def test_format_price_many_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    format(repo, 465)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_format_price_edge_2(price):
    price.label = "cart-441"

    format(price)

    assert price.state == "done"


def test_format_price_large_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    format(repo, 312)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
