"""Near-miss: the same targets rebuilt in each phase, as home-assistant's
`cast/test_media_player.py:955` rebuilds its `cast_status`. Each target counts once:
`status`, `status.read.return_value` and the patched `shop.clock`. Analysed, never
run."""

from unittest import mock

import pytest
from shop import Player, Status

pytestmark = pytest.mark.unit


def test_volume_follows_each_status():
    player = Player()
    seen = []

    status = mock.MagicMock(spec=Status)
    status.read.return_value = {"level": 0.5, "muted": False}
    with mock.patch("shop.clock", autospec=True):
        seen.append(player.on_status(status))

    status = mock.MagicMock(spec=Status)
    status.read.return_value = {"level": 0.2, "muted": True}
    with mock.patch("shop.clock", autospec=True):
        seen.append(player.on_status(status))

    status = mock.MagicMock(spec=Status)
    status.read.return_value = {"level": 0.0, "muted": False}
    with mock.patch("shop.clock", autospec=True):
        seen.append(player.on_status(status))

    status = mock.MagicMock(spec=Status)
    status.read.return_value = {"control": "fixed"}
    with mock.patch("shop.clock", autospec=True):
        seen.append(player.on_status(status))

    assert seen == [0.5, 0.2, 0.0, None]
