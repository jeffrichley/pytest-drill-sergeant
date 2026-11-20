"""Tests for reports invoice handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_invoice, merge

pytestmark = pytest.mark.unit


@pytest.fixture
def invoice():
    return make_invoice()


def test_merge_invoice_single_0():
    invoice = make_invoice(amount=24, count=96)

    result = merge(invoice)

    assert result.total == 2304


def test_merge_invoice_single_1_runs():
    merge(make_invoice())


def test_merge_invoice_empty_2():
    invoice = make_invoice(amount=71, count=28)

    result = merge(invoice)

    assert result.total == 1988


def test_merge_invoice_large_3():
    invoice = make_invoice(amount=65, count=10)

    result = merge(invoice)

    assert result.total == 650


def test_merge_invoice_edge_4():
    invoice = make_invoice(amount=6, count=86)

    result = merge(invoice)

    assert result.total == 516


def test_merge_invoice_many_5(invoice):
    invoice.label = "user-733"

    merge(invoice)

    assert invoice.state == "held"


def test_merge_invoice_empty_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    merge(repo, 332)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_invoice_single_7():
    invoice = make_invoice(amount=26, count=60)

    result = merge(invoice)

    assert result.total == 1560
