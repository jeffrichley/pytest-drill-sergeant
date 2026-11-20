"""Tests for catalog address handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_address, build

pytestmark = pytest.mark.unit


@pytest.fixture
def address():
    return make_address()


def test_build_address_basic_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    build(repo, 52)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(42, 84), (29, 58), (9, 18)])
def test_build_address_large_1(value, expected):
    assert build(value) == expected


def test_build_address_single_2_rejects_bad_input():
    with pytest.raises(ValueError, match="address"):
        build(None)


def test_build_address_empty_3(address):
    address.label = "refund-235"

    build(address)

    assert address.state == "done"


def test_build_address_edge_4_works():
    result = build(make_address())
    assert result is not None


def test_build_address_single_5():
    address = make_address(amount=3, count=51)

    result = build(address)

    assert result.total == 153


@pytest.mark.parametrize(("value", "expected"), [(11, 22), (1, 2), (12, 24)])
def test_build_address_many_6(value, expected):
    assert build(value) == expected


def test_build_address_empty_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    build(repo, 53)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
