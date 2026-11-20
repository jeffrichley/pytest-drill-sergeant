"""Near-miss across files: the billing setup in euros. Analysed, never run."""

import pytest
from billing import Account, Gateway, Ledger

pytestmark = pytest.mark.unit


def test_refund_credits_the_account():
    ledger = Ledger(currency="EUR")
    gateway = Gateway(ledger, retries=2)
    account = Account(gateway, limit=500)
    account.refund(100)
    assert account.balance == 100
