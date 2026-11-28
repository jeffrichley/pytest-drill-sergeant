"""Near-miss: `reset_mock()` between phases, as home-assistant's
`sonos/test_plex_playback.py:26` calls it. Resetting a mock scripts nothing, and
neither does calling one. Analysed, never run."""

from unittest.mock import Mock, patch

import pytest
from shop import Server, play

pytestmark = pytest.mark.unit


def test_play_queues_each_kind():
    server = Mock(spec=Server)
    lookup = server.lookup
    played = []
    with (
        patch("shop.get_server", autospec=True, return_value=server),
        patch("shop.Queue.add", autospec=True) as add,
        patch("shop.Player.shuffle", autospec=True) as shuffle,
    ):
        played.append(play("album"))

        lookup.reset_mock()
        add.reset_mock()
        shuffle.reset_mock()
        played.append(play("album", shuffle=True))

        lookup.reset_mock()
        add.reset_mock()
        shuffle.reset_mock()
        lookup()
        played.append(play("playlist"))

        lookup.reset_mock()
        add.reset_mock()
        shuffle.reset_mock(return_value=True)
        played.append(play("track"))

    assert played == ["album", "album", "playlist", "track"]
