"""Tests for notifications event handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_event, compute


@pytest.fixture
def event():
    return make_event()


def test_compute_event_edge_0(event):
    event.label = "refund-636"

    compute(event)

    assert event.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(1, 2), (14, 28), (45, 90)])
def test_compute_event_single_1(value, expected):
    assert compute(value) == expected


def test_compute_event_many_2():
    event = make_event(amount=38, count=59)

    result = compute(event)

    assert result.total == 2242


def test_compute_event_single_3(event):
    event.label = "invoice-454"

    compute(event)

    assert event.state == "held"
