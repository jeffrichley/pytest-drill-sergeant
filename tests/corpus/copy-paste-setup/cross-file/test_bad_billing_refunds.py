"""The third copy of the billing setup, reported on the first. Analysed, never
run."""

from billing import Account, Gateway, Ledger


def test_refund_credits_the_account():
    ledger = Ledger(currency="USD")
    gateway = Gateway(ledger, retries=2)
    account = Account(gateway, limit=500)
    account.refund(100)
    assert account.balance == 100
