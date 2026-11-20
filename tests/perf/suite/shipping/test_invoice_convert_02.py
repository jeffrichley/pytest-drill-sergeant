"""Tests for shipping invoice handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_invoice, convert

pytestmark = pytest.mark.unit


@pytest.fixture
def invoice():
    return make_invoice()


def test_convert_invoice_single_0():
    invoice = make_invoice(amount=86, count=24)

    result = convert(invoice)

    assert result.total == 2064


@pytest.mark.parametrize(("value", "expected"), [(46, 92), (41, 82), (16, 32)])
def test_convert_invoice_edge_1(value, expected):
    assert convert(value) == expected


def test_convert_invoice_basic_2_rejects_bad_input():
    with pytest.raises(ValueError, match="invoice"):
        convert(None)


def test_convert_invoice_large_3(invoice):
    invoice.label = "invoice-756"

    convert(invoice)

    assert invoice.state == "held"


def test_convert_invoice_single_4():
    invoice = make_invoice(amount=69, count=26)

    result = convert(invoice)

    assert result.total == 1794


def test_convert_invoice_many_5(invoice):
    invoice.label = "price-959"

    convert(invoice)

    assert invoice.state == "held"
