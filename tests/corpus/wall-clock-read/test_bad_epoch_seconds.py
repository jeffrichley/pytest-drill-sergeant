"""Tests that read epoch seconds to time the code or stamp a token.

Analysed, never run.
"""

import time
from time import time_ns

import pytest
from tokens import issue_token

pytestmark = pytest.mark.unit


def test_token_carries_the_issue_time():
    token = issue_token()
    assert abs(token.issued_at - time.time()) < 1  # expect: DS802


def test_issue_is_fast():
    start = time_ns()  # expect: DS802
    issue_token()
    assert time_ns() - start < 1_000_000  # expect: DS802


def test_token_carries_the_local_hour():
    token = issue_token()
    assert token.hour == time.localtime().tm_hour  # expect: DS802
