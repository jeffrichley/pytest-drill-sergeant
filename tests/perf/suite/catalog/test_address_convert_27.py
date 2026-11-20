"""Tests for catalog address handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_address, convert

pytestmark = pytest.mark.unit


@pytest.fixture
def address():
    return make_address()


def test_convert_address_basic_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    convert(repo, 295)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_address_many_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    convert(repo, 213)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(1, 2), (10, 20), (45, 90)])
def test_convert_address_many_2(value, expected):
    assert convert(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(41, 82), (3, 6), (29, 58)])
def test_convert_address_single_3(value, expected):
    assert convert(value) == expected


def test_convert_address_empty_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    convert(repo, 341)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
