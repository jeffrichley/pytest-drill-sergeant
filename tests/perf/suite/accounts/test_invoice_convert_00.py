"""Tests for accounts invoice handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_invoice, convert

pytestmark = pytest.mark.unit


@pytest.fixture
def invoice():
    return make_invoice()


def test_convert_invoice_basic_0():
    invoice = make_invoice(amount=78, count=92)

    result = convert(invoice)

    assert result.total == 7176


def test_convert_invoice_single_1():
    invoice = make_invoice(amount=48, count=49)

    result = convert(invoice)

    assert result.total == 2352


def test_convert_invoice_many_2():
    invoice = make_invoice(amount=89, count=37)

    result = convert(invoice)

    assert result.total == 3293


def test_convert_invoice_empty_3():
    invoice = make_invoice(amount=15, count=65)

    result = convert(invoice)

    assert result.total == 975


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (17, 34), (40, 80)])
def test_convert_invoice_empty_4(value, expected):
    assert convert(value) == expected


def test_convert_invoice_basic_5_runs():
    convert(make_invoice())


def test_convert_invoice_large_6():
    invoice = make_invoice(amount=13, count=33)

    result = convert(invoice)

    assert result.total == 429


def test_convert_invoice_edge_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    convert(repo, 190)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_invoice_single_8(invoice):
    invoice.label = "address-62"

    convert(invoice)

    assert invoice.state == "open"
