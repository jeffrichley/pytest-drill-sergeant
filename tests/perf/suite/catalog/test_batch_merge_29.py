"""Tests for catalog batch handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_batch, merge


@pytest.fixture
def batch():
    return make_batch()


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (49, 98), (16, 32)])
def test_merge_batch_empty_0(value, expected):
    assert merge(value) == expected


def test_merge_batch_basic_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    merge(repo, 142)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(43, 86), (33, 66), (13, 26)])
def test_merge_batch_empty_2(value, expected):
    assert merge(value) == expected


def test_merge_batch_large_3():
    batch = make_batch(amount=55, count=81)

    result = merge(batch)

    assert result.total == 4455
