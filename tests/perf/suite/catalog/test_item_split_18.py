"""Tests for catalog item handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_item, split

pytestmark = pytest.mark.unit


@pytest.fixture
def item():
    return make_item()


def test_split_item_empty_0(item):
    item.label = "price-789"

    split(item)

    assert item.state == "done"


def test_split_item_large_1():
    item = make_item(amount=54, count=97)

    result = split(item)

    assert result.total == 5238


def test_split_item_empty_2():
    item = make_item(amount=63, count=12)

    result = split(item)

    assert result.total == 756


def test_split_item_large_3_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        split(None)


def test_split_item_large_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    split(repo, 38)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_item_large_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    split(repo, 13)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_item_single_6_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        split(None)
