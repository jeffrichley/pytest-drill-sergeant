"""Near-misses: private names that are the test's own, or used in setup rather than
asserted. Analysed, never run."""

import pytest
from app import Cache

pytestmark = pytest.mark.unit


class TestCache:
    def setup_method(self):
        self._cache = Cache()

    def test_miss_then_hit(self):
        self._cache.get("k")
        assert self._cache.hits == 1


def test_fake_clock_injected_in_setup(fake_clock):
    cache = Cache()
    cache._clock = fake_clock
    cache.get("k")
    assert cache.age("k") == 0


def test_public_stats():
    cache = Cache()
    cache.get("k")
    assert cache.stats().misses == 1
