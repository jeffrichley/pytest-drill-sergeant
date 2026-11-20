"""Tests for billing item handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_item, parse


@pytest.fixture
def item():
    return make_item()


def test_parse_item_many_0():
    item = make_item(amount=27, count=85)

    result = parse(item)

    assert result.total == 2295


def test_parse_item_edge_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    parse(repo, 10)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(12, 24), (25, 50), (46, 92)])
def test_parse_item_edge_2(value, expected):
    assert parse(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(48, 96), (15, 30), (11, 22)])
def test_parse_item_edge_3(value, expected):
    assert parse(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(10, 20), (24, 48), (48, 96)])
def test_parse_item_large_4(value, expected):
    assert parse(value) == expected


def test_parse_item_empty_5():
    item = make_item(amount=37, count=48)

    result = parse(item)

    assert result.total == 1776


def test_parse_item_many_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    parse(repo, 7)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_item_edge_7():
    item = make_item(amount=30, count=16)

    result = parse(item)

    assert result.total == 480


@pytest.mark.parametrize(("value", "expected"), [(2, 4), (36, 72), (8, 16)])
def test_parse_item_many_8(value, expected):
    assert parse(value) == expected
