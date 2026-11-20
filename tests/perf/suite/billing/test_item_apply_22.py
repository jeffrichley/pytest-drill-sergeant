"""Tests for billing item handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_item, apply

pytestmark = pytest.mark.unit


@pytest.fixture
def item():
    return make_item()


def test_apply_item_single_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    apply(repo, 331)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_item_single_1_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        apply(None)


def test_apply_item_single_2(item):
    item.label = "user-606"

    apply(item)

    assert item.state == "held"


def test_apply_item_edge_3_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        apply(None)


def test_apply_item_edge_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    apply(repo, 92)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_item_many_5(item):
    item.label = "item-407"

    apply(item)

    assert item.state == "open"


def test_apply_item_many_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    apply(repo, 189)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
