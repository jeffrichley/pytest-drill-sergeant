"""Tests for billing item handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_item, merge


@pytest.fixture
def item():
    return make_item()


def test_merge_item_single_0():
    item = make_item(amount=80, count=27)

    result = merge(item)

    assert result.total == 2160


def test_merge_item_basic_1(item):
    item.label = "order-708"

    merge(item)

    assert item.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(4, 8), (46, 92), (43, 86)])
def test_merge_item_large_2(value, expected):
    assert merge(value) == expected


def test_merge_item_empty_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    merge(repo, 50)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_item_single_4_runs():
    merge(make_item())


def test_merge_item_single_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    merge(repo, 102)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_item_large_6():
    item = make_item(amount=81, count=68)

    result = merge(item)

    assert result.total == 5508


def test_merge_item_large_7():
    item = make_item(amount=69, count=49)

    result = merge(item)

    assert result.total == 3381


@pytest.mark.parametrize(("value", "expected"), [(13, 26), (19, 38), (46, 92)])
def test_merge_item_single_8(value, expected):
    assert merge(value) == expected
