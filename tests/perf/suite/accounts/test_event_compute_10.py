"""Tests for accounts event handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_event, compute

pytestmark = pytest.mark.unit


@pytest.fixture
def event():
    return make_event()


def test_compute_event_empty_0():
    event = make_event(amount=73, count=10)

    result = compute(event)

    assert result.total == 730


def test_compute_event_basic_1():
    event = make_event(amount=39, count=97)

    result = compute(event)

    assert result.total == 3783


def test_compute_event_many_2():
    event = make_event(amount=62, count=48)

    result = compute(event)

    assert result.total == 2976


def test_compute_event_empty_3():
    event = make_event(amount=54, count=70)

    result = compute(event)

    assert result.total == 3780
