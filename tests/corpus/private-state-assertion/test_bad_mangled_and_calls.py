"""Private state checked through name-mangled attributes and assertion calls.
Analysed, never run."""

import unittest

from app import Account, Service


def test_mangled_balance():
    account = Account(10)
    assert account._Account__balance == 10  # expect: DS602


def test_private_method_was_called(mocker):
    service = Service(client=mocker.Mock())
    service.run()
    service._client.send.assert_called_once()  # expect: DS602


def test_private_method_result():
    assert Service()._build_url("x") == "https://example.com/x"  # expect: DS602


class TestAccount(unittest.TestCase):
    def test_balance(self):
        account = Account(10)
        self.assertEqual(account._balance, 10)  # expect: DS602
