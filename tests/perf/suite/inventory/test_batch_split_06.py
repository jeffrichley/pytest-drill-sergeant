"""Tests for inventory batch handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_batch, split

pytestmark = pytest.mark.unit


@pytest.fixture
def batch():
    return make_batch()


@pytest.mark.parametrize(("value", "expected"), [(15, 30), (38, 76), (14, 28)])
def test_split_batch_many_0(value, expected):
    assert split(value) == expected


def test_split_batch_basic_1():
    batch = make_batch(amount=89, count=41)

    result = split(batch)

    assert result.total == 3649


def test_split_batch_empty_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    split(repo, 475)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_batch_empty_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    split(repo, 302)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
