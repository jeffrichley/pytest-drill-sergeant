"""Interleaving inside a `mock.patch`, and with a loop as the second act. Analysed,
never run."""

from unittest import mock


def test_counter_under_patch(counter):
    with mock.patch("time.time", return_value=0):
        counter.tick()
        assert counter.value == 1
        counter.reset()  # expect: DS104
        assert counter.value == 0


def test_queue(queue, jobs):
    queue.push("a")
    assert len(queue) == 1
    for job in jobs:  # expect: DS104
        queue.push(job)
    assert len(queue) == 1 + len(jobs)
