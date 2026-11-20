"""Tests for auth item handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_item, build


@pytest.fixture
def item():
    return make_item()


def test_build_item_single_0_works():
    result = build(make_item())
    assert result is not None


def test_build_item_many_1():
    item = make_item(amount=95, count=66)

    result = build(item)

    assert result.total == 6270


def test_build_item_single_2(item):
    item.label = "invoice-841"

    build(item)

    assert item.state == "held"


def test_build_item_large_3():
    item = make_item(amount=72, count=45)

    result = build(item)

    assert result.total == 3240


def test_build_item_large_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    build(repo, 324)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(40, 80), (41, 82), (4, 8)])
def test_build_item_many_5(value, expected):
    assert build(value) == expected


def test_build_item_empty_6():
    item = make_item(amount=85, count=13)

    result = build(item)

    assert result.total == 1105
