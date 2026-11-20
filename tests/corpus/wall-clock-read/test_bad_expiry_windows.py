"""Tests that compare against today's date and the current time, so they pass or fail
depending on when they run. Analysed, never run.
"""

from datetime import date, datetime, timedelta

import pytest
from billing import Invoice, Subscription

pytestmark = pytest.mark.unit


def test_invoice_is_due_in_thirty_days():
    invoice = Invoice.issue()
    assert invoice.due == date.today() + timedelta(days=30)  # expect: DS802


def test_subscription_is_active():
    sub = Subscription(ends=datetime(2027, 1, 1))
    assert sub.active_at(datetime.now())  # expect: DS802


class TestAudit:
    def test_stamp_is_recent(self, audit):
        entry = audit.record("login")
        assert (datetime.utcnow() - entry.at).total_seconds() < 1  # expect: DS802
