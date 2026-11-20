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
