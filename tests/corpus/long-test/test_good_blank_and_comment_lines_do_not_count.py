"""Near-miss: a test laid out as DS108 asks, with AAA comments, explaining comments and
blank lines between its sections. They take it past 50 lines from `def` to its last
line, but only lines with code count, and it has 19. Analysed, never run."""

import pytest
from billing import Ledger

pytestmark = pytest.mark.unit


def test_month_end_closes_the_ledger(accounts):
    # Arrange
    # A ledger with one account per kind the month-end close treats differently:
    # an asset, a liability, an income and an expense account.
    ledger = Ledger(period="2026-10")

    # The asset account carries its balance into the next period.
    ledger.open(accounts.cash)

    # The liability account does too.
    ledger.open(accounts.loans)

    # Income and expense accounts are closed into retained earnings.
    ledger.open(accounts.sales)
    ledger.open(accounts.rent)

    # One posting each, so every account has a balance to close.
    ledger.post(accounts.cash, 1000)
    ledger.post(accounts.loans, -400)
    ledger.post(accounts.sales, -900)
    ledger.post(accounts.rent, 300)

    # Nothing is posted to the retained earnings account itself: the close
    # computes its balance from the income and expense accounts, and a
    # posting here would be counted twice.

    # The period is still open, so the close below is allowed.

    # Act
    # Close the month. This is the behaviour under test.
    closed = ledger.close_month()

    # Assert
    # Assets and liabilities carry forward unchanged.
    assert closed.balance(accounts.cash) == 1000

    assert closed.balance(accounts.loans) == -400

    # Income and expense accounts are zeroed.
    assert closed.balance(accounts.sales) == 0

    assert closed.balance(accounts.rent) == 0

    # Their net lands in retained earnings: 900 income less 300 expense.
    assert closed.retained_earnings == 600

    # The new period is the next month.
    assert closed.period == "2026-11"

    # The old ledger is locked against further postings.
    assert ledger.locked

    # And the close is recorded once.
    assert ledger.closes == 1

    # Closing a second time would raise; another test covers that, so it is not
    # repeated here.
