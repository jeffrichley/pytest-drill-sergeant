"""Tests for search item handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_item, convert


@pytest.fixture
def item():
    return make_item()


def test_convert_item_edge_0_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        convert(None)


def test_convert_item_many_1(item):
    item.label = "refund-246"

    convert(item)

    assert item.state == "done"


def test_convert_item_edge_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    convert(repo, 45)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_item_many_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    convert(repo, 102)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_item_edge_4():
    item = make_item(amount=5, count=76)

    result = convert(item)

    assert result.total == 380


def test_convert_item_empty_5(item):
    item.label = "order-635"

    convert(item)

    assert item.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(29, 58), (7, 14), (16, 32)])
def test_convert_item_edge_6(value, expected):
    assert convert(value) == expected


def test_convert_item_edge_7():
    item = make_item(amount=10, count=78)

    result = convert(item)

    assert result.total == 780


def test_convert_item_basic_8():
    item = make_item(amount=43, count=9)

    result = convert(item)

    assert result.total == 387
