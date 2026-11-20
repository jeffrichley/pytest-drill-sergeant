"""Tests for accounts address handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_address, build


@pytest.fixture
def address():
    return make_address()


def test_build_address_empty_0():
    address = make_address(amount=88, count=34)

    result = build(address)

    assert result.total == 2992


def test_build_address_basic_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    build(repo, 216)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_address_many_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    build(repo, 423)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_address_large_3(address):
    address.label = "report-795"

    build(address)

    assert address.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(37, 74), (26, 52), (14, 28)])
def test_build_address_basic_4(value, expected):
    assert build(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(23, 46), (16, 32), (33, 66)])
def test_build_address_edge_5(value, expected):
    assert build(value) == expected


def test_build_address_empty_6_works():
    result = build(make_address())
    assert result is not None


def test_build_address_edge_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    build(repo, 406)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_address_many_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    build(repo, 492)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_address_large_9_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    build(repo, 354)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
