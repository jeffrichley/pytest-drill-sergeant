"""Reasonless marks and calls reached through aliases, on a class and the module.

Analysed, never run.
"""

import sys

import pytest as pt
from pytest import mark as m
from pytest import xfail
from queueing import Queue

pytestmark = [m.skipif(sys.platform == "darwin")]  # expect: DS401


@pt.mark.xfail(sys.version_info < (3, 12))  # expect: DS401
class TestQueue:
    def test_queue_is_first_in_first_out(self):
        queue = Queue()
        queue.put(1)
        queue.put(2)
        assert [queue.get(), queue.get()] == [1, 2]


def test_queue_blocks_when_full():
    queue = Queue(maxsize=1)
    if not queue.supports_blocking():
        xfail("")  # expect: DS401
    queue.put(1)
    assert queue.full()
