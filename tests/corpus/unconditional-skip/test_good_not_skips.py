"""Near-misses: a strict xfail is not a skip, and a `skip` of the code's own is not
pytest's. Analysed, never run.
"""

import pytest
from playlist import Playlist

pytestmark = pytest.mark.unit


@pytest.mark.xfail(reason="shuffle repeats songs, #41", strict=True)
def test_shuffle_never_repeats_a_song():
    songs = Playlist(["a", "b", "c"]).shuffle()
    assert sorted(songs) == ["a", "b", "c"]


def test_skip_moves_to_the_next_song():
    playlist = Playlist(["a", "b"])
    playlist.skip()
    assert playlist.current() == "b"


def skip(playlist):
    return playlist.advance(2)


def test_local_skip_advances_two_songs():
    assert skip(Playlist(["a", "b", "c"])) == "c"
