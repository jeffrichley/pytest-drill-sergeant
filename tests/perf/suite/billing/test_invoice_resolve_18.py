"""Tests for billing invoice handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_invoice, resolve

pytestmark = pytest.mark.unit


@pytest.fixture
def invoice():
    return make_invoice()


def test_resolve_invoice_single_0_rejects_bad_input():
    with pytest.raises(ValueError, match="invoice"):
        resolve(None)


@pytest.mark.parametrize(("value", "expected"), [(48, 96), (18, 36), (37, 74)])
def test_resolve_invoice_empty_1(value, expected):
    assert resolve(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(19, 38), (30, 60), (28, 56)])
def test_resolve_invoice_basic_2(value, expected):
    assert resolve(value) == expected


def test_resolve_invoice_edge_3(invoice):
    invoice.label = "report-469"

    resolve(invoice)

    assert invoice.state == "open"


def test_resolve_invoice_large_4(invoice):
    invoice.label = "price-892"

    resolve(invoice)

    assert invoice.state == "done"


def test_resolve_invoice_empty_5():
    invoice = make_invoice(amount=34, count=89)

    result = resolve(invoice)

    assert result.total == 3026


def test_resolve_invoice_empty_6_works():
    result = resolve(make_invoice())
    assert result is not None


def test_resolve_invoice_many_7(invoice):
    invoice.label = "batch-653"

    resolve(invoice)

    assert invoice.state == "held"


def test_resolve_invoice_basic_8():
    invoice = make_invoice(amount=23, count=39)

    result = resolve(invoice)

    assert result.total == 897


def test_resolve_invoice_single_9(invoice):
    invoice.label = "item-279"

    resolve(invoice)

    assert invoice.state == "held"
