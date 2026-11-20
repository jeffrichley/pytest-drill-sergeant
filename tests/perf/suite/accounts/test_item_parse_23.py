"""Tests for accounts item handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_item, parse


@pytest.fixture
def item():
    return make_item()


def test_parse_item_basic_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    parse(repo, 245)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(36, 72), (37, 74), (31, 62)])
def test_parse_item_many_1(value, expected):
    assert parse(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(47, 94), (48, 96), (4, 8)])
def test_parse_item_many_2(value, expected):
    assert parse(value) == expected


def test_parse_item_single_3():
    item = make_item(amount=86, count=43)

    result = parse(item)

    assert result.total == 3698


def test_parse_item_basic_4():
    item = make_item(amount=85, count=24)

    result = parse(item)

    assert result.total == 2040
