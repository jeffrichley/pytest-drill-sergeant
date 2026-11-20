"""Near-miss: bodies alike but for their values, under different decorators or
fixtures, which one parametrized function can't hold. Analysed, never run."""

from datetime import date

import pytest
from billing import Invoice
from freezegun import freeze_time

pytestmark = pytest.mark.unit


@freeze_time("2026-01-01")
def test_invoice_dated_new_year():
    assert Invoice.issue().date == date(2026, 1, 1)


@freeze_time("2026-07-04")
def test_invoice_dated_midsummer():
    assert Invoice.issue().date == date(2026, 7, 4)


def test_invoice_in_euros(eu_customer):
    assert Invoice.issue().currency == "EUR"


def test_invoice_in_dollars(us_customer):
    assert Invoice.issue().currency == "USD"
