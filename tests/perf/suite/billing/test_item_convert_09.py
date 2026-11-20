"""Tests for billing item handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_item, convert


@pytest.fixture
def item():
    return make_item()


def test_convert_item_single_0():
    item = make_item(amount=54, count=3)

    result = convert(item)

    assert result.total == 162


def test_convert_item_edge_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    convert(repo, 281)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_item_many_2_runs():
    convert(make_item())


def test_convert_item_basic_3():
    item = make_item(amount=54, count=36)

    result = convert(item)

    assert result.total == 1944


@pytest.mark.parametrize(("value", "expected"), [(6, 12), (46, 92), (44, 88)])
def test_convert_item_single_4(value, expected):
    assert convert(value) == expected
