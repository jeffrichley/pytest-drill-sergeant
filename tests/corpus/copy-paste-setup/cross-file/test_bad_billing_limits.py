"""The second copy of the billing setup, reported on the first. Analysed, never
run."""

from billing import Account, Gateway, Ledger


def test_charge_over_the_limit_is_refused():
    ledger = Ledger(currency="USD")
    gateway = Gateway(ledger, retries=2)
    account = Account(gateway, limit=500)
    assert account.charge(900) is False
