"""A class and a module whose marks are all something else, and a category marker
on a helper that is not the test. Analysed, never run.
"""

import sys

import pytest
from ledger import Ledger

pytestmark = [pytest.mark.skipif(sys.platform == "win32", reason="POSIX paths")]


@pytest.mark.slow
class TestLedger:
    pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

    def test_ledger_balances_to_zero(self):  # expect: DS901
        assert Ledger().balance() == 0

    class TestPostings:
        def test_posting_moves_the_balance(self):  # expect: DS901
            ledger = Ledger()
            ledger.post(5)
            assert ledger.balance() == 5


@pytest.mark.unit
def helper_ledger():
    return Ledger(opening=10)


def test_opening_balance_is_kept():  # expect: DS901
    assert helper_ledger().balance() == 10
