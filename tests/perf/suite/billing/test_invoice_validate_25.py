"""Tests for billing invoice handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_invoice, validate

pytestmark = pytest.mark.unit


@pytest.fixture
def invoice():
    return make_invoice()


def test_validate_invoice_edge_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    validate(repo, 28)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_invoice_many_1():
    invoice = make_invoice(amount=7, count=4)

    result = validate(invoice)

    assert result.total == 28


@pytest.mark.parametrize(("value", "expected"), [(35, 70), (13, 26), (49, 98)])
def test_validate_invoice_basic_2(value, expected):
    assert validate(value) == expected


def test_validate_invoice_many_3_works():
    result = validate(make_invoice())
    assert result is not None


def test_validate_invoice_empty_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    validate(repo, 84)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
