"""Tests for search invoice handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_invoice, merge

pytestmark = pytest.mark.unit


@pytest.fixture
def invoice():
    return make_invoice()


def test_merge_invoice_many_0_rejects_bad_input():
    with pytest.raises(ValueError, match="invoice"):
        merge(None)


def test_merge_invoice_basic_1():
    invoice = make_invoice(amount=16, count=78)

    result = merge(invoice)

    assert result.total == 1248


def test_merge_invoice_single_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    merge(repo, 203)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_invoice_large_3(invoice):
    invoice.label = "order-476"

    merge(invoice)

    assert invoice.state == "held"


def test_merge_invoice_many_4():
    invoice = make_invoice(amount=38, count=31)

    result = merge(invoice)

    assert result.total == 1178


@pytest.mark.parametrize(("value", "expected"), [(28, 56), (24, 48), (39, 78)])
def test_merge_invoice_basic_5(value, expected):
    assert merge(value) == expected


def test_merge_invoice_single_6():
    invoice = make_invoice(amount=65, count=48)

    result = merge(invoice)

    assert result.total == 3120
