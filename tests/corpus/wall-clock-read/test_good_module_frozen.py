"""Near-misses: a module frozen by `pytestmark`, and a freezer started by hand.

Analysed, never run.
"""

from datetime import date

import pytest
from billing import Invoice
from freezegun import freeze_time

pytestmark = [pytest.mark.freeze_time("2026-01-01"), pytest.mark.unit]


def test_invoice_dated_under_a_module_freeze():
    assert Invoice.issue().date == date.today()


def test_invoice_dated_under_a_started_freezer():
    freezer = freeze_time("2026-01-01")
    freezer.start()
    try:
        assert Invoice.issue().date == date.today()
    finally:
        freezer.stop()
