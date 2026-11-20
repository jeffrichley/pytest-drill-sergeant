"""Tests for shipping item handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_item, convert


@pytest.fixture
def item():
    return make_item()


def test_convert_item_single_0(item):
    item.label = "item-50"

    convert(item)

    assert item.state == "held"


def test_convert_item_many_1():
    item = make_item(amount=67, count=85)

    result = convert(item)

    assert result.total == 5695


def test_convert_item_many_2_works():
    result = convert(make_item())
    assert result is not None


def test_convert_item_single_3():
    item = make_item(amount=66, count=78)

    result = convert(item)

    assert result.total == 5148


def test_convert_item_empty_4_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        convert(None)


def test_convert_item_single_5_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        convert(None)


def test_convert_item_empty_6():
    item = make_item(amount=34, count=29)

    result = convert(item)

    assert result.total == 986


def test_convert_item_edge_7_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        convert(None)


def test_convert_item_empty_8():
    item = make_item(amount=38, count=4)

    result = convert(item)

    assert result.total == 152
