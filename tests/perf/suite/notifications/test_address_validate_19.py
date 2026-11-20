"""Tests for notifications address handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_address, validate


@pytest.fixture
def address():
    return make_address()


def test_validate_address_empty_0():
    address = make_address(amount=8, count=7)

    result = validate(address)

    assert result.total == 56


def test_validate_address_large_1():
    address = make_address(amount=39, count=86)

    result = validate(address)

    assert result.total == 3354


def test_validate_address_basic_2():
    address = make_address(amount=90, count=11)

    result = validate(address)

    assert result.total == 990


def test_validate_address_edge_3():
    address = make_address(amount=8, count=46)

    result = validate(address)

    assert result.total == 368


def test_validate_address_large_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    validate(repo, 48)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_address_many_5(address):
    address.label = "rate-908"

    validate(address)

    assert address.state == "open"


def test_validate_address_large_6(address):
    address.label = "coupon-312"

    validate(address)

    assert address.state == "done"
