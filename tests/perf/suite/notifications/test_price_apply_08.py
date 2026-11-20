"""Tests for notifications price handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_price, apply

pytestmark = pytest.mark.unit


@pytest.fixture
def price():
    return make_price()


def test_apply_price_single_0():
    price = make_price(amount=88, count=35)

    result = apply(price)

    assert result.total == 3080


def test_apply_price_edge_1_rejects_bad_input():
    with pytest.raises(ValueError, match="price"):
        apply(None)


def test_apply_price_large_2():
    price = make_price(amount=15, count=72)

    result = apply(price)

    assert result.total == 1080


def test_apply_price_large_3():
    price = make_price(amount=42, count=71)

    result = apply(price)

    assert result.total == 2982


def test_apply_price_many_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    apply(repo, 258)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_price_large_5():
    price = make_price(amount=29, count=32)

    result = apply(price)

    assert result.total == 928


def test_apply_price_single_6():
    price = make_price(amount=53, count=92)

    result = apply(price)

    assert result.total == 4876
