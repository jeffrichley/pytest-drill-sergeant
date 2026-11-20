"""Tests for shipping order handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_order, render

pytestmark = pytest.mark.unit


@pytest.fixture
def order():
    return make_order()


def test_render_order_basic_0():
    order = make_order(amount=18, count=7)

    result = render(order)

    assert result.total == 126


def test_render_order_edge_1():
    order = make_order(amount=19, count=21)

    result = render(order)

    assert result.total == 399


def test_render_order_large_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    render(repo, 491)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_order_empty_3_runs():
    render(make_order())


def test_render_order_empty_4():
    order = make_order(amount=50, count=32)

    result = render(order)

    assert result.total == 1600
