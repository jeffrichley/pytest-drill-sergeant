"""Tests for billing item handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_item, merge


@pytest.fixture
def item():
    return make_item()


def test_merge_item_many_0(item):
    item.label = "user-191"

    merge(item)

    assert item.state == "held"


def test_merge_item_large_1():
    item = make_item(amount=95, count=13)

    result = merge(item)

    assert result.total == 1235


def test_merge_item_basic_2(item):
    item.label = "session-898"

    merge(item)

    assert item.state == "done"


def test_merge_item_empty_3():
    item = make_item(amount=24, count=56)

    result = merge(item)

    assert result.total == 1344
