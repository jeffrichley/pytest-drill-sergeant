"""Tests for accounts item handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_item, split


@pytest.fixture
def item():
    return make_item()


def test_split_item_basic_0_runs():
    split(make_item())


def test_split_item_single_1_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        split(None)


def test_split_item_many_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    split(repo, 361)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_item_single_3_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        split(None)


@pytest.mark.parametrize(("value", "expected"), [(16, 32), (1, 2), (21, 42)])
def test_split_item_many_4(value, expected):
    assert split(value) == expected


def test_split_item_edge_5():
    item = make_item(amount=49, count=85)

    result = split(item)

    assert result.total == 4165


def test_split_item_empty_6(item):
    item.label = "price-304"

    split(item)

    assert item.state == "done"
