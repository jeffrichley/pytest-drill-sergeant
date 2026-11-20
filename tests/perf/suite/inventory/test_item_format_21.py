"""Tests for inventory item handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_item, format

pytestmark = pytest.mark.unit


@pytest.fixture
def item():
    return make_item()


def test_format_item_single_0():
    item = make_item(amount=23, count=79)

    result = format(item)

    assert result.total == 1817


def test_format_item_single_1():
    item = make_item(amount=21, count=13)

    result = format(item)

    assert result.total == 273


def test_format_item_basic_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    format(repo, 358)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(6, 12), (46, 92), (25, 50)])
def test_format_item_edge_3(value, expected):
    assert format(value) == expected


def test_format_item_basic_4():
    item = make_item(amount=87, count=6)

    result = format(item)

    assert result.total == 522


@pytest.mark.parametrize(("value", "expected"), [(25, 50), (31, 62), (41, 82)])
def test_format_item_large_5(value, expected):
    assert format(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(36, 72), (43, 86), (39, 78)])
def test_format_item_edge_6(value, expected):
    assert format(value) == expected


def test_format_item_basic_7():
    item = make_item(amount=56, count=67)

    result = format(item)

    assert result.total == 3752
