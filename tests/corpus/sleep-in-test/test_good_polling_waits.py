"""Near-misses: a poll that waits on the condition itself, and a zero-second sleep that
only yields. Analysed, never run.
"""

import time

import pytest
from worker import Worker

pytestmark = pytest.mark.unit


def test_worker_finishes_within_a_deadline():
    worker = Worker()
    worker.start()
    deadline = time.monotonic() + 5
    while not worker.done and time.monotonic() < deadline:
        time.sleep(0.01)
    assert worker.done


def test_worker_runs_after_yielding():
    worker = Worker()
    worker.start()
    time.sleep(0)
    assert worker.started


def test_worker_finishes_within_a_bounded_number_of_polls():
    worker = Worker()
    worker.start()
    for _ in range(500):
        if worker.done:
            break
        time.sleep(0.01)
    assert worker.done


def test_worker_finishes_polled_by_a_loop_that_returns():
    worker = Worker()
    worker.start()
    for _ in range(500):
        if worker.done:
            return
        time.sleep(0.01)
    pytest.fail("worker never finished")


def test_workers_finish_polled_by_a_return_in_an_inner_loop():
    workers = [Worker(), Worker()]
    for _ in range(500):
        for worker in workers:
            if worker.done:
                return
        time.sleep(0.01)
    pytest.fail("no worker finished")


def test_worker_finishes_polled_through_a_helper():
    worker = Worker()

    def settle():
        time.sleep(0.01)

    worker.start()
    while not worker.done:
        settle()
    assert worker.done
