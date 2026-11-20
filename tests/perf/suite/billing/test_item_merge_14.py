"""Tests for billing item handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_item, merge

pytestmark = pytest.mark.unit


@pytest.fixture
def item():
    return make_item()


@pytest.mark.parametrize(("value", "expected"), [(1, 2), (42, 84), (40, 80)])
def test_merge_item_many_0(value, expected):
    assert merge(value) == expected


def test_merge_item_single_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    merge(repo, 112)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_item_single_2():
    item = make_item(amount=32, count=79)

    result = merge(item)

    assert result.total == 2528


@pytest.mark.parametrize(("value", "expected"), [(35, 70), (5, 10), (7, 14)])
def test_merge_item_single_3(value, expected):
    assert merge(value) == expected


def test_merge_item_many_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    merge(repo, 251)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(1, 2), (38, 76), (27, 54)])
def test_merge_item_single_5(value, expected):
    assert merge(value) == expected


def test_merge_item_edge_6(item):
    item.label = "coupon-781"

    merge(item)

    assert item.state == "done"


def test_merge_item_basic_7():
    item = make_item(amount=67, count=20)

    result = merge(item)

    assert result.total == 1340


def test_merge_item_single_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    merge(repo, 184)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
