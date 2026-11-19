"""Near-misses: `try` with nothing caught, and swallowing outside any test.
Analysed, never run."""

import pytest


def connect():
    return object()


def test_try_finally_catches_nothing():
    connection = connect()
    try:
        assert connection is not None
    finally:
        del connection


@pytest.fixture
def server():
    try:
        yield connect()
    except Exception:
        pass


def best_effort_cleanup(path):
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def test_uses_a_swallowing_helper(tmp_path, server):
    best_effort_cleanup(tmp_path / "gone")
    assert server is not None


class Helper:
    def test_not_collected(self):
        try:
            connect()
        except Exception:
            pass
