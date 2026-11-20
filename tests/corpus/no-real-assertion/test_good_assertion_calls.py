"""Near-misses: assertions made through calls, not `assert` statements. Analysed,
never run."""

import unittest
from unittest import mock

from pandas.testing import assert_frame_equal


def notify(sender, message):
    sender.send(message)


def test_mock_verification_is_an_assertion():
    sender = mock.Mock()
    notify(sender, "hi")
    sender.send.assert_called_once_with("hi")


def test_assertion_helper_is_an_assertion(frame, expected):
    assert_frame_equal(frame.dropna(), expected)


class TestUnittestStyle(unittest.TestCase):
    def test_assert_equal(self):
        self.assertEqual(int("3"), 3)


def test_truthy_constant_beside_a_real_assertion():
    assert True
    assert int("4") == 4


def test_assertion_in_a_local_helper():
    def check(text):
        assert int(text) > 0

    check("5")
