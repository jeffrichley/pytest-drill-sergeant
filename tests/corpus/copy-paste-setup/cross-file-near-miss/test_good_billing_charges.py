"""Near-miss across files, which this folder's group is analysed as together: each
file builds the billing setup with its own currency, so no block is pasted.
Analysed, never run."""

import pytest
from billing import Account, Gateway, Ledger

pytestmark = pytest.mark.unit


def test_charge_debits_the_account():
    ledger = Ledger(currency="CAD")
    gateway = Gateway(ledger, retries=2)
    account = Account(gateway, limit=500)
    account.charge(100)
    assert account.balance == -100
