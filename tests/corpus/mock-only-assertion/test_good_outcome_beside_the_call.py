"""Near-misses: a mock verification beside an assertion on the outcome. Analysed,
never run."""

from unittest import mock

import pytest
from shop import Repo, Sender, notify, register


def test_send_and_result():
    sender = mock.Mock(spec=Sender)
    result = notify(sender, "hi")
    sender.send.assert_called_once_with("hi")
    assert result.delivered == 1


def test_raises_and_never_sends():
    sender = mock.Mock(spec=Sender)
    with pytest.raises(ValueError, match="empty"):
        notify(sender, "")
    sender.send.assert_not_called()


def test_call_count_against_the_outcome():
    repo = mock.create_autospec(Repo, instance=True)
    saved = register(repo, ["a", "b"])
    assert repo.save.call_count == len(saved)
