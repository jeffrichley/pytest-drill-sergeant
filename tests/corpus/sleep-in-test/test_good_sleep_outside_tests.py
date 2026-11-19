"""Near-misses: real sleeps outside any test, and a sleep passed but not called.

Analysed, never run.
"""

import time

import pytest
from worker import Worker


def wait_for_worker(worker):
    while not worker.done:
        time.sleep(0.01)


@pytest.fixture
def started_worker():
    worker = Worker()
    worker.start()
    time.sleep(0.1)
    return worker


def test_worker_done(started_worker):
    wait_for_worker(started_worker)
    assert started_worker.done


def test_passes_sleep_without_calling_it():
    worker = Worker(sleep=time.sleep)
    assert worker.sleep is time.sleep
