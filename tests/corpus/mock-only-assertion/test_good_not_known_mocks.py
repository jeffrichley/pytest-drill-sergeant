"""Near-misses: values named like mocks, or verified like mocks, whose kind the file
never shows. A name is the author's word, not the code's. Analysed, never run."""

import pytest
from shop import compute, make_sender, notify

pytestmark = pytest.mark.unit


def test_fixture_named_like_a_mock(mock_sender):
    notify(mock_sender, "hi")
    mock_sender.send.assert_called_once_with("hi")


def test_helper_made_double():
    sender = make_sender()
    notify(sender, "hi")
    sender.send.assert_called_once_with("hi")


def test_local_named_like_a_mock():
    mock_result = compute(2)
    assert mock_result == 4
