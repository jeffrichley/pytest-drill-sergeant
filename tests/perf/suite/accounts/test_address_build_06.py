"""Tests for accounts address handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_address, build


@pytest.fixture
def address():
    return make_address()


def test_build_address_single_0(address):
    address.label = "price-261"

    build(address)

    assert address.state == "held"


def test_build_address_edge_1():
    address = make_address(amount=87, count=57)

    result = build(address)

    assert result.total == 4959


def test_build_address_many_2(address):
    address.label = "session-48"

    build(address)

    assert address.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(34, 68), (44, 88), (47, 94)])
def test_build_address_many_3(value, expected):
    assert build(value) == expected


def test_build_address_single_4():
    address = make_address(amount=8, count=51)

    result = build(address)

    assert result.total == 408


def test_build_address_large_5():
    address = make_address(amount=48, count=64)

    result = build(address)

    assert result.total == 3072


def test_build_address_edge_6(address):
    address.label = "session-190"

    build(address)

    assert address.state == "held"
