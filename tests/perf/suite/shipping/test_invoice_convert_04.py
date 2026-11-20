"""Tests for shipping invoice handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_invoice, convert

pytestmark = pytest.mark.unit


@pytest.fixture
def invoice():
    return make_invoice()


def test_convert_invoice_empty_0(invoice):
    invoice.label = "coupon-454"

    convert(invoice)

    assert invoice.state == "held"


def test_convert_invoice_single_1():
    invoice = make_invoice(amount=9, count=91)

    result = convert(invoice)

    assert result.total == 819


def test_convert_invoice_many_2_rejects_bad_input():
    with pytest.raises(ValueError, match="invoice"):
        convert(None)


def test_convert_invoice_empty_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    convert(repo, 436)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_invoice_edge_4_runs():
    convert(make_invoice())
