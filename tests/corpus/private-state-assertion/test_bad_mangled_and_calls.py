"""Private state checked through name-mangled attributes and assertion calls.
Analysed, never run."""

import unittest

import pytest
from app import Account, Service

pytestmark = pytest.mark.unit


def test_mangled_balance():
    account = Account(10)
    assert account._Account__balance == 10  # expect: DS602


def test_private_method_was_called(mocker):
    service = Service(client=mocker.Mock())
    service.run()
    service._client.send.assert_called_once()  # expect: DS602


def test_private_method_result():
    assert Service()._build_url("x") == "https://example.com/x"  # expect: DS602


def test_raises_matching_a_private_message():
    with pytest.raises(ValueError, match=Service._timeout_message):  # expect: DS602
        Service().run()


def test_warns_matching_a_private_message():
    with pytest.warns(UserWarning, match=Service._slow_message):  # expect: DS602
        Service().run()


def test_raises_assertion_error_on_private_state():
    service = Service()
    service.run()
    if service._retries:
        raise AssertionError(service._retries)  # expect: DS602


class TestAccount(unittest.TestCase):
    def test_balance(self):
        account = Account(10)
        self.assertEqual(account._balance, 10)  # expect: DS602
