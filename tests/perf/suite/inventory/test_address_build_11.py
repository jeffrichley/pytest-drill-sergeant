"""Tests for inventory address handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_address, build

pytestmark = pytest.mark.unit


@pytest.fixture
def address():
    return make_address()


def test_build_address_basic_0():
    address = make_address(amount=5, count=20)

    result = build(address)

    assert result.total == 100


def test_build_address_large_1():
    address = make_address(amount=53, count=26)

    result = build(address)

    assert result.total == 1378


def test_build_address_edge_2():
    address = make_address(amount=15, count=57)

    result = build(address)

    assert result.total == 855


def test_build_address_basic_3_rejects_bad_input():
    with pytest.raises(ValueError, match="address"):
        build(None)


def test_build_address_empty_4_rejects_bad_input():
    with pytest.raises(ValueError, match="address"):
        build(None)


def test_build_address_edge_5():
    address = make_address(amount=39, count=82)

    result = build(address)

    assert result.total == 3198


def test_build_address_many_6(address):
    address.label = "cart-490"

    build(address)

    assert address.state == "held"


def test_build_address_empty_7():
    address = make_address(amount=16, count=72)

    result = build(address)

    assert result.total == 1152


def test_build_address_many_8():
    address = make_address(amount=83, count=87)

    result = build(address)

    assert result.total == 7221
