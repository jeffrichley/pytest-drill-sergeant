"""Near-misses: functions named `sleep` that are not the real one.

Analysed, never run.
"""

import pytest
from worker import Worker

pytestmark = pytest.mark.unit


def sleep(seconds):
    return seconds


def test_module_level_function_named_sleep():
    assert sleep(2) == 2


def test_nested_function_named_sleep():
    calls = []

    def sleep(seconds):
        calls.append(seconds)

    Worker(sleep=sleep).retry()
    assert calls == [1, 2, 4]


def test_fixture_named_sleep(sleep):
    Worker(sleep=sleep).retry()
    sleep.assert_called()


def test_clock_object_with_a_sleep_method(fake_clock):
    fake_clock.sleep(10)
    assert fake_clock.now() == 10
