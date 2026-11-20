"""Near-misses: things called `Mock`, `patch` or `mocker` that the file doesn't show
to be the mock library. Analysed, never run."""

from unittest import mock

import pytest
from doubles import Mock, patch
from shop import label, notify

pytestmark = pytest.mark.unit


def make_sender():
    return mock.Mock()


def test_own_double_library():
    sender = Mock()
    with patch("shop.today"):
        assert notify(sender, "hi").delivered == 1


def test_fixture_named_mock(mock):
    sender = mock.Mock()
    assert notify(sender, "hi").delivered == 1


def test_mocker_not_taken():
    assert label(mocker.Mock()) == "Today"


mocker = object()
