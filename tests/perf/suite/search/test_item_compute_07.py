"""Tests for search item handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_item, compute


@pytest.fixture
def item():
    return make_item()


def test_compute_item_edge_0_runs():
    compute(make_item())


@pytest.mark.parametrize(("value", "expected"), [(33, 66), (17, 34), (46, 92)])
def test_compute_item_edge_1(value, expected):
    assert compute(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(7, 14), (25, 50), (24, 48)])
def test_compute_item_single_2(value, expected):
    assert compute(value) == expected


def test_compute_item_many_3():
    item = make_item(amount=92, count=66)

    result = compute(item)

    assert result.total == 6072


def test_compute_item_large_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    compute(repo, 497)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_item_many_5_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        compute(None)
