"""The catalog's example (#26): waiting out a real timeout with `time.sleep`.

Analysed, never run.
"""

import time

import pytest
from tokens import is_expired, issue_token

pytestmark = pytest.mark.unit


def test_token_expires_after_its_ttl():
    token = issue_token(ttl=1)
    time.sleep(1.1)  # expect: DS801
    assert is_expired(token)


class TestCache:
    def test_entry_is_evicted(self, cache):
        cache.put("k", "v", ttl=0.5)
        time.sleep(0.6)  # expect: DS801
        assert cache.get("k") is None


def test_each_token_expires_after_its_ttl():
    for ttl in (0.1, 0.2):  # expect: DS107
        token = issue_token(ttl=ttl)
        time.sleep(ttl + 0.05)  # expect: DS801
        assert is_expired(token)


def test_tokens_expire_after_a_break_that_only_leaves_the_inner_loop():
    for ttl in (0.1, 0.2):  # expect: DS107
        token = issue_token(ttl=ttl)
        for _ in range(3):
            if token:
                break
        time.sleep(ttl + 0.05)  # expect: DS801
        assert is_expired(token)
