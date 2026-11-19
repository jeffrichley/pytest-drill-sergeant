"""Asserts before the act, inside a `with` block that isn't an assertion. Analysed,
never run."""

from unittest import mock


def test_refresh_token(session):
    with mock.patch("time.time", return_value=0):
        assert session.token is None
        session.refresh()  # expect: DS103


def test_retry(fetcher):
    with mock.patch("time.sleep"):
        assert fetcher.attempts == 0
    fetcher.fetch("/a")  # expect: DS103
