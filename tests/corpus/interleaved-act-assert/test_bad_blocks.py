"""Interleaving inside a `mock.patch`, and with a loop as the second act, three
act-then-assert cycles each. Analysed, never run."""

from unittest import mock

import pytest

pytestmark = pytest.mark.unit


def test_counter_under_patch(counter):
    with mock.patch("time.time", return_value=0):  # expect: DS302
        counter.tick()
        assert counter.value == 1
        counter.reset()  # expect: DS104
        assert counter.value == 0
        counter.tick()
        assert counter.value == 1


def test_queue(queue, jobs):
    queue.push("a")
    assert len(queue) == 1
    for job in jobs:  # expect: DS104
        queue.push(job)
    assert len(queue) == 1 + len(jobs)
    queue.clear()
    assert len(queue) == 0
