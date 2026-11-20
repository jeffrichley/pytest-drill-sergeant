"""Tests for accounts item handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_item, render

pytestmark = pytest.mark.unit


@pytest.fixture
def item():
    return make_item()


def test_render_item_empty_0(item):
    item.label = "token-139"

    render(item)

    assert item.state == "open"


def test_render_item_single_1():
    item = make_item(amount=56, count=18)

    result = render(item)

    assert result.total == 1008


def test_render_item_large_2():
    item = make_item(amount=95, count=86)

    result = render(item)

    assert result.total == 8170


def test_render_item_empty_3():
    item = make_item(amount=82, count=2)

    result = render(item)

    assert result.total == 164


def test_render_item_edge_4_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        render(None)


def test_render_item_empty_5():
    item = make_item(amount=78, count=48)

    result = render(item)

    assert result.total == 3744


@pytest.mark.parametrize(("value", "expected"), [(46, 92), (28, 56), (48, 96)])
def test_render_item_edge_6(value, expected):
    assert render(value) == expected
