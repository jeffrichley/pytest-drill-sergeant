"""The catalog's example (#26): waiting out a real timeout with `time.sleep`.

Analysed, never run.
"""

import time

from tokens import is_expired, issue_token


def test_token_expires_after_its_ttl():
    token = issue_token(ttl=1)
    time.sleep(1.1)  # expect: DS801
    assert is_expired(token)


class TestCache:
    def test_entry_is_evicted(self, cache):
        cache.put("k", "v", ttl=0.5)
        time.sleep(0.6)  # expect: DS801
        assert cache.get("k") is None
