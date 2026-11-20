"""Tests for catalog address handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_address, resolve


@pytest.fixture
def address():
    return make_address()


def test_resolve_address_edge_0():
    address = make_address(amount=19, count=2)

    result = resolve(address)

    assert result.total == 38


def test_resolve_address_single_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    resolve(repo, 76)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(6, 12), (7, 14), (3, 6)])
def test_resolve_address_many_2(value, expected):
    assert resolve(value) == expected


def test_resolve_address_basic_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    resolve(repo, 55)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_address_many_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    resolve(repo, 398)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
