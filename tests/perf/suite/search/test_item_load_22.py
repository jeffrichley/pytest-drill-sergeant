"""Tests for search item handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_item, load


@pytest.fixture
def item():
    return make_item()


def test_load_item_single_0():
    item = make_item(amount=7, count=85)

    result = load(item)

    assert result.total == 595


def test_load_item_single_1(item):
    item.label = "coupon-124"

    load(item)

    assert item.state == "done"


def test_load_item_many_2(item):
    item.label = "batch-677"

    load(item)

    assert item.state == "done"


def test_load_item_many_3(item):
    item.label = "address-737"

    load(item)

    assert item.state == "done"


def test_load_item_many_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    load(repo, 171)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(3, 6), (24, 48), (35, 70)])
def test_load_item_many_5(value, expected):
    assert load(value) == expected


def test_load_item_many_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    load(repo, 483)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_load_item_edge_7_works():
    result = load(make_item())
    assert result is not None


def test_load_item_basic_8():
    item = make_item(amount=2, count=73)

    result = load(item)

    assert result.total == 146
