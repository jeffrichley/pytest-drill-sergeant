"""Tests for catalog address handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_address, merge


@pytest.fixture
def address():
    return make_address()


def test_merge_address_many_0_rejects_bad_input():
    with pytest.raises(ValueError, match="address"):
        merge(None)


def test_merge_address_single_1():
    address = make_address(amount=1, count=48)

    result = merge(address)

    assert result.total == 48


def test_merge_address_basic_2():
    address = make_address(amount=27, count=33)

    result = merge(address)

    assert result.total == 891


def test_merge_address_edge_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    merge(repo, 342)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_address_edge_4():
    address = make_address(amount=10, count=44)

    result = merge(address)

    assert result.total == 440


def test_merge_address_single_5():
    address = make_address(amount=51, count=4)

    result = merge(address)

    assert result.total == 204


@pytest.mark.parametrize(("value", "expected"), [(31, 62), (9, 18), (40, 80)])
def test_merge_address_large_6(value, expected):
    assert merge(value) == expected


def test_merge_address_edge_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    merge(repo, 179)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_address_edge_8():
    address = make_address(amount=9, count=27)

    result = merge(address)

    assert result.total == 243
