"""Tests for billing price handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_price, convert


@pytest.fixture
def price():
    return make_price()


def test_convert_price_empty_0():
    price = make_price(amount=21, count=79)

    result = convert(price)

    assert result.total == 1659


def test_convert_price_large_1():
    price = make_price(amount=81, count=17)

    result = convert(price)

    assert result.total == 1377


def test_convert_price_single_2():
    price = make_price(amount=58, count=40)

    result = convert(price)

    assert result.total == 2320


def test_convert_price_edge_3():
    price = make_price(amount=80, count=50)

    result = convert(price)

    assert result.total == 4000


def test_convert_price_empty_4():
    price = make_price(amount=13, count=76)

    result = convert(price)

    assert result.total == 988


def test_convert_price_edge_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    convert(repo, 52)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_price_single_6_rejects_bad_input():
    with pytest.raises(ValueError, match="price"):
        convert(None)
