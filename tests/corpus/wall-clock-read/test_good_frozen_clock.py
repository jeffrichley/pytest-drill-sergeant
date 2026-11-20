"""Near-misses: wall-clock reads under a frozen clock, which return a fixed time.

Analysed, never run.
"""

import time
from datetime import date, datetime

import pytest
import time_machine
from billing import Invoice
from freezegun import freeze_time

pytestmark = pytest.mark.unit


@freeze_time("2026-01-01")
def test_invoice_dated_under_a_frozen_decorator():
    assert Invoice.issue().date == date.today()


def test_invoice_dated_inside_a_frozen_block():
    with freeze_time("2026-01-01"):
        assert Invoice.issue().issued == datetime.now()


@time_machine.travel("2026-01-01")
def test_invoice_stamped_under_time_machine():
    assert Invoice.issue().stamp == time.time()


@pytest.mark.freeze_time("2026-01-01")
def test_invoice_dated_under_the_pytest_freezer_marker():
    assert Invoice.issue().date == date.today()


def test_invoice_dated_with_the_freezer_fixture(freezer):
    freezer.move_to("2026-01-01")
    assert Invoice.issue().date == date.today()


def test_invoice_dated_with_the_time_machine_fixture(time_machine):
    time_machine.move_to("2026-01-01")
    assert Invoice.issue().date == date.today()


@freeze_time("2026-01-01")
class TestFrozenClass:
    def test_invoice_dated_in_a_frozen_class(self):
        assert Invoice.issue().date == date.today()
