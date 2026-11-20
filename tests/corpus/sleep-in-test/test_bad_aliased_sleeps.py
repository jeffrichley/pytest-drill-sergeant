"""Sleeps reached through import aliases. Analysed, never run."""

import time as t
from time import sleep
from time import sleep as pause

import pytest
from worker import Worker

pytestmark = pytest.mark.unit


def test_worker_finishes():
    worker = Worker()
    worker.start()
    sleep(2)  # expect: DS801
    assert worker.done


def test_worker_retries():
    worker = Worker(retries=3)
    worker.start()
    pause(0.5)  # expect: DS801
    t.sleep(0.5)  # expect: DS801
    assert worker.attempts == 3


def test_sleep_imported_inside_the_test():
    import time

    worker = Worker()
    worker.start()
    time.sleep(1)  # expect: DS801
    assert worker.done
