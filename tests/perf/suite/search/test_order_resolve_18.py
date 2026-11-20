"""Tests for search order handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_order, resolve

pytestmark = pytest.mark.unit


@pytest.fixture
def order():
    return make_order()


def test_resolve_order_basic_0():
    order = make_order(amount=61, count=8)

    result = resolve(order)

    assert result.total == 488


@pytest.mark.parametrize(("value", "expected"), [(2, 4), (7, 14), (37, 74)])
def test_resolve_order_edge_1(value, expected):
    assert resolve(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(13, 26), (39, 78), (23, 46)])
def test_resolve_order_empty_2(value, expected):
    assert resolve(value) == expected


def test_resolve_order_single_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    resolve(repo, 224)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
