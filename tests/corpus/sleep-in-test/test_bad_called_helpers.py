"""Sleeps in helpers the test defines and calls itself, so the test sleeps.

Analysed, never run.
"""

import asyncio
import time

import pytest
from worker import Worker

pytestmark = pytest.mark.unit


def test_a_helper_the_test_calls():
    worker = Worker()

    def settle():
        time.sleep(0.5)  # expect: DS801

    worker.start()
    settle()
    assert worker.done


@pytest.mark.asyncio
async def test_an_async_helper_the_test_awaits():
    worker = Worker()

    async def settle():
        await asyncio.sleep(0.5)  # expect: DS801

    worker.start()
    await settle()
    assert worker.done


def test_a_helper_called_through_an_alias():
    worker = Worker()

    def settle():
        time.sleep(0.5)  # expect: DS801

    wait = settle
    worker.start()
    wait()
    assert worker.done


@pytest.mark.asyncio
async def test_a_helper_called_inside_create_task():
    worker = Worker()

    async def settle():
        await asyncio.sleep(0.5)  # expect: DS801

    worker.start()
    await asyncio.create_task(settle())
    assert worker.done


def test_a_lambda_bound_and_called():
    worker = Worker()
    settle = lambda: time.sleep(0.5)  # noqa: E731 -- a bound lambda is the case  # expect: DS801
    worker.start()
    settle()
    assert worker.done


def test_a_helper_called_by_a_helper_the_test_calls():
    worker = Worker()

    def pause():
        time.sleep(0.5)  # expect: DS801

    def settle():
        pause()

    worker.start()
    settle()
    assert worker.done


@pytest.mark.asyncio
async def test_a_top_level_negative_proof_sleep():
    worker = Worker()
    worker.start()
    await asyncio.sleep(0.05)  # expect: DS801
    assert worker.asked == []


def test_an_alias_keeps_the_helper_when_its_name_is_rebound():
    worker = Worker()

    def settle():
        time.sleep(0.5)  # expect: DS801

    wait = settle
    settle = worker.join
    worker.start()
    wait()
    assert worker.done


def test_a_lambda_called_where_it_is_written():
    worker = Worker()
    worker.start()
    (lambda: time.sleep(0.5))()  # expect: DS801
    assert worker.done
