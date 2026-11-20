"""Assertions that reach into an object's private attributes. Seeded from the
failure-modes catalog (#22). Analysed, never run."""

import pytest
from app import Cache, Queue

pytestmark = pytest.mark.unit


def test_cache_stores_the_key():
    cache = Cache()
    cache.get("k")
    assert cache._store == {"k": None}  # expect: DS602
    assert cache._hits == 0  # expect: DS602


def test_queue_holds_two_items():
    queue = Queue()
    queue.put(1)
    queue.put(2)
    assert len(queue._items) == 2  # expect: DS602


def test_two_private_names_in_one_assert():
    cache = Cache()
    assert cache._hits + cache._misses == 0  # expect: DS602


def test_private_state_inside_a_generator(caches):
    assert all(c._store == {} for c in caches)  # expect: DS602
