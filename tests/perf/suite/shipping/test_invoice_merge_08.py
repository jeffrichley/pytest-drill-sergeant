"""Tests for shipping invoice handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_invoice, merge


@pytest.fixture
def invoice():
    return make_invoice()


def test_merge_invoice_basic_0():
    invoice = make_invoice(amount=65, count=80)

    result = merge(invoice)

    assert result.total == 5200


def test_merge_invoice_edge_1_runs():
    merge(make_invoice())


def test_merge_invoice_many_2():
    invoice = make_invoice(amount=62, count=83)

    result = merge(invoice)

    assert result.total == 5146


@pytest.mark.parametrize(("value", "expected"), [(34, 68), (21, 42), (15, 30)])
def test_merge_invoice_single_3(value, expected):
    assert merge(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(27, 54), (26, 52), (5, 10)])
def test_merge_invoice_single_4(value, expected):
    assert merge(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(18, 36), (14, 28), (37, 74)])
def test_merge_invoice_edge_5(value, expected):
    assert merge(value) == expected
