"""Tests for shipping order handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_order, render

pytestmark = pytest.mark.unit


@pytest.fixture
def order():
    return make_order()


def test_render_order_basic_0():
    order = make_order(amount=66, count=90)

    result = render(order)

    assert result.total == 5940


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (13, 26), (42, 84)])
def test_render_order_single_1(value, expected):
    assert render(value) == expected


def test_render_order_many_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    render(repo, 393)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_order_large_3():
    order = make_order(amount=67, count=3)

    result = render(order)

    assert result.total == 201


def test_render_order_edge_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    render(repo, 139)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(44, 88), (41, 82), (29, 58)])
def test_render_order_basic_5(value, expected):
    assert render(value) == expected
