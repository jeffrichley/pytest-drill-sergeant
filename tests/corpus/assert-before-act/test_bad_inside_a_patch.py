"""Asserts before the act, inside a `with` block that isn't an assertion. Analysed,
never run."""

from unittest import mock

import pytest

pytestmark = pytest.mark.unit


def test_refresh_token(session):
    with mock.patch("time.time", return_value=0):  # expect: DS302
        assert session.token is None
        session.refresh()  # expect: DS103


def test_retry(fetcher):
    with mock.patch("time.sleep"):  # expect: DS302
        assert fetcher.attempts == 0
    fetcher.fetch("/a")  # expect: DS103
