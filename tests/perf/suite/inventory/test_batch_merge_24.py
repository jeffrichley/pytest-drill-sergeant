"""Tests for inventory batch handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_batch, merge


@pytest.fixture
def batch():
    return make_batch()


def test_merge_batch_large_0():
    batch = make_batch(amount=73, count=62)

    result = merge(batch)

    assert result.total == 4526


def test_merge_batch_single_1():
    batch = make_batch(amount=83, count=93)

    result = merge(batch)

    assert result.total == 7719


def test_merge_batch_single_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    merge(repo, 431)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_batch_large_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    merge(repo, 110)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
