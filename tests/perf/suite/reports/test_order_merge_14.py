"""Tests for reports order handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_order, merge


@pytest.fixture
def order():
    return make_order()


def test_merge_order_empty_0_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        merge(None)


def test_merge_order_single_1_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        merge(None)


def test_merge_order_single_2_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        merge(None)


@pytest.mark.parametrize(("value", "expected"), [(9, 18), (22, 44), (35, 70)])
def test_merge_order_large_3(value, expected):
    assert merge(value) == expected


def test_merge_order_many_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    merge(repo, 246)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(33, 66), (6, 12), (5, 10)])
def test_merge_order_empty_5(value, expected):
    assert merge(value) == expected


def test_merge_order_empty_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    merge(repo, 483)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
