"""Tests for shipping price handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_price, load


@pytest.fixture
def price():
    return make_price()


def test_load_price_large_0_rejects_bad_input():
    with pytest.raises(ValueError, match="price"):
        load(None)


def test_load_price_large_1_rejects_bad_input():
    with pytest.raises(ValueError, match="price"):
        load(None)


def test_load_price_edge_2():
    price = make_price(amount=89, count=79)

    result = load(price)

    assert result.total == 7031


def test_load_price_large_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    load(repo, 470)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_load_price_many_4():
    price = make_price(amount=74, count=79)

    result = load(price)

    assert result.total == 5846


def test_load_price_empty_5():
    price = make_price(amount=38, count=17)

    result = load(price)

    assert result.total == 646
