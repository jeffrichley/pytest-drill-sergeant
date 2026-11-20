"""Tests for shipping order handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_order, split

pytestmark = pytest.mark.unit


@pytest.fixture
def order():
    return make_order()


def test_split_order_empty_0():
    order = make_order(amount=83, count=25)

    result = split(order)

    assert result.total == 2075


def test_split_order_many_1_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        split(None)


def test_split_order_edge_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    split(repo, 471)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(39, 78), (36, 72), (32, 64)])
def test_split_order_single_3(value, expected):
    assert split(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(40, 80), (23, 46), (17, 34)])
def test_split_order_basic_4(value, expected):
    assert split(value) == expected


def test_split_order_many_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    split(repo, 60)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(29, 58), (16, 32), (41, 82)])
def test_split_order_basic_6(value, expected):
    assert split(value) == expected
