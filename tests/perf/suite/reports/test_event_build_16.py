"""Tests for reports event handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_event, build


@pytest.fixture
def event():
    return make_event()


def test_build_event_large_0():
    event = make_event(amount=34, count=50)

    result = build(event)

    assert result.total == 1700


def test_build_event_basic_1_rejects_bad_input():
    with pytest.raises(ValueError, match="event"):
        build(None)


def test_build_event_empty_2_rejects_bad_input():
    with pytest.raises(ValueError, match="event"):
        build(None)


def test_build_event_basic_3():
    event = make_event(amount=92, count=71)

    result = build(event)

    assert result.total == 6532


def test_build_event_single_4(event):
    event.label = "session-759"

    build(event)

    assert event.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(25, 50), (14, 28), (39, 78)])
def test_build_event_edge_5(value, expected):
    assert build(value) == expected
