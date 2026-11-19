"""Near-misses: between assertions there is only cleanup, an expected exception or
a helper definition, never a second act. Analysed, never run."""

import pytest


def test_withdraw(account):
    account.withdraw(5)
    assert account.balance == 5
    with pytest.raises(ValueError, match="insufficient"):
        account.withdraw(50)
    assert account.balance == 5


def test_mock_reset_between_checks(notifier, sender):
    notifier.notify("hi")
    sender.send.assert_called_once_with("hi")
    sender.reset_mock()
    assert sender.send.call_count == 0


def test_helper_defined_between(store):
    store.put("k", 1)
    assert store.get("k") == 1

    def lookup(key):
        return store.get(key)

    assert lookup("k") == 1
