"""Tests for auth item handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_item, resolve

pytestmark = pytest.mark.unit


@pytest.fixture
def item():
    return make_item()


@pytest.mark.parametrize(("value", "expected"), [(5, 10), (29, 58), (18, 36)])
def test_resolve_item_basic_0(value, expected):
    assert resolve(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(16, 32), (44, 88), (13, 26)])
def test_resolve_item_basic_1(value, expected):
    assert resolve(value) == expected


def test_resolve_item_large_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    resolve(repo, 125)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_item_many_3():
    item = make_item(amount=50, count=86)

    result = resolve(item)

    assert result.total == 4300


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (18, 36), (48, 96)])
def test_resolve_item_single_4(value, expected):
    assert resolve(value) == expected


def test_resolve_item_edge_5_works():
    result = resolve(make_item())
    assert result is not None
