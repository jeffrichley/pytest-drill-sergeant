"""Near-misses: an act after an assertion whose outcome is still checked, by its own
assertion, by `pytest.raises`, or by a later assertion on what it returned.
Analysed, never run."""

import pytest


def test_withdraw_too_much(account):
    assert account.balance == 10
    with pytest.raises(ValueError, match="insufficient"):
        account.withdraw(20)


def test_deposit_returns_the_balance(account):
    assert account.balance == 10
    balance = account.deposit(5)
    assert balance == 15


def test_parse_in_the_assert(parser):
    assert parser.ready
    assert parser.parse("1") == 1
