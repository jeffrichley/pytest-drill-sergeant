"""Tests for notifications invoice handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_invoice, resolve

pytestmark = pytest.mark.unit


@pytest.fixture
def invoice():
    return make_invoice()


def test_resolve_invoice_empty_0(invoice):
    invoice.label = "user-406"

    resolve(invoice)

    assert invoice.state == "done"


def test_resolve_invoice_large_1_rejects_bad_input():
    with pytest.raises(ValueError, match="invoice"):
        resolve(None)


def test_resolve_invoice_many_2(invoice):
    invoice.label = "event-870"

    resolve(invoice)

    assert invoice.state == "open"


def test_resolve_invoice_large_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    resolve(repo, 433)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_invoice_many_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    resolve(repo, 481)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_invoice_single_5():
    invoice = make_invoice(amount=98, count=13)

    result = resolve(invoice)

    assert result.total == 1274
