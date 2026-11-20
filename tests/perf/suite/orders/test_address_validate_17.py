"""Tests for orders address handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_address, validate


@pytest.fixture
def address():
    return make_address()


@pytest.mark.parametrize(("value", "expected"), [(16, 32), (43, 86), (15, 30)])
def test_validate_address_many_0(value, expected):
    assert validate(value) == expected


def test_validate_address_empty_1():
    address = make_address(amount=43, count=11)

    result = validate(address)

    assert result.total == 473


def test_validate_address_single_2():
    address = make_address(amount=46, count=58)

    result = validate(address)

    assert result.total == 2668


def test_validate_address_many_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    validate(repo, 297)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_address_basic_4(address):
    address.label = "address-132"

    validate(address)

    assert address.state == "open"


def test_validate_address_many_5():
    address = make_address(amount=5, count=63)

    result = validate(address)

    assert result.total == 315


def test_validate_address_basic_6():
    address = make_address(amount=40, count=18)

    result = validate(address)

    assert result.total == 720
