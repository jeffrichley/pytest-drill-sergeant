"""Near-misses: between assertions there is only an expected exception, a helper
definition, output, or one of pytest's own fixtures taken as a parameter, never a
second act. Analysed, never run."""

import logging

import pytest

pytestmark = pytest.mark.unit


def test_withdraw(account):
    account.withdraw(5)
    assert account.balance == 5
    with pytest.raises(ValueError, match="insufficient"):
        account.withdraw(50)
    assert account.balance == 5


def test_fixtures_and_output_between_checks(capsys, monkeypatch, greeter):
    greeter.greet("Ada")
    assert capsys.readouterr().out == "hi Ada\n"
    capsys.readouterr()
    monkeypatch.setenv("LANG", "C")
    logging.info("greeted")
    print("checked")
    assert greeter.greeted == ["Ada"]


def test_helper_defined_between(store):
    store.put("k", 1)
    assert store.get("k") == 1

    def lookup(key):
        return store.get(key)

    assert lookup("k") == 1
