"""Near-miss across files: the billing setup in euros. Analysed, never run."""

from billing import Account, Gateway, Ledger


def test_refund_credits_the_account():
    ledger = Ledger(currency="EUR")
    gateway = Gateway(ledger, retries=2)
    account = Account(gateway, limit=500)
    account.refund(100)
    assert account.balance == 100
