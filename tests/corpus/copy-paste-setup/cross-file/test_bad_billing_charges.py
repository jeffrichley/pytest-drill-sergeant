"""One setup block pasted across three files, which this folder's group is
analysed as together: the finding is on the first occurrence. Analysed, never
run."""

from billing import Account, Gateway, Ledger


def test_charge_debits_the_account():
    ledger = Ledger(currency="USD")  # expect: DS501
    gateway = Gateway(ledger, retries=2)
    account = Account(gateway, limit=500)
    account.charge(100)
    assert account.balance == -100
