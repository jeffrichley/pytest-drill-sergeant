"""Tests for billing address handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_address, apply


@pytest.fixture
def address():
    return make_address()


@pytest.mark.parametrize(("value", "expected"), [(2, 4), (30, 60), (20, 40)])
def test_apply_address_basic_0(value, expected):
    assert apply(value) == expected


def test_apply_address_large_1():
    address = make_address(amount=41, count=46)

    result = apply(address)

    assert result.total == 1886


def test_apply_address_single_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    apply(repo, 381)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_address_many_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_address()

    apply(repo, 31)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_address_many_4():
    address = make_address(amount=17, count=24)

    result = apply(address)

    assert result.total == 408


def test_apply_address_single_5():
    address = make_address(amount=22, count=59)

    result = apply(address)

    assert result.total == 1298


def test_apply_address_basic_6_works():
    result = apply(make_address())
    assert result is not None
