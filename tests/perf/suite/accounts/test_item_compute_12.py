"""Tests for accounts item handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_item, compute


@pytest.fixture
def item():
    return make_item()


def test_compute_item_basic_0_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        compute(None)


@pytest.mark.parametrize(("value", "expected"), [(10, 20), (33, 66), (17, 34)])
def test_compute_item_empty_1(value, expected):
    assert compute(value) == expected


def test_compute_item_edge_2_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        compute(None)


def test_compute_item_single_3():
    item = make_item(amount=65, count=4)

    result = compute(item)

    assert result.total == 260


def test_compute_item_large_4():
    item = make_item(amount=71, count=64)

    result = compute(item)

    assert result.total == 4544


def test_compute_item_single_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    compute(repo, 123)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_item_basic_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    compute(repo, 246)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_item_basic_7(item):
    item.label = "refund-585"

    compute(item)

    assert item.state == "done"
