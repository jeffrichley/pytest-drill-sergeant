"""Tests for shipping event handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_event, format


@pytest.fixture
def event():
    return make_event()


def test_format_event_single_0(event):
    event.label = "report-553"

    format(event)

    assert event.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(19, 38), (8, 16), (48, 96)])
def test_format_event_single_1(value, expected):
    assert format(value) == expected


def test_format_event_edge_2(event):
    event.label = "order-3"

    format(event)

    assert event.state == "held"


def test_format_event_many_3():
    event = make_event(amount=99, count=78)

    result = format(event)

    assert result.total == 7722


def test_format_event_large_4_works():
    result = format(make_event())
    assert result is not None


@pytest.mark.parametrize(("value", "expected"), [(39, 78), (32, 64), (4, 8)])
def test_format_event_many_5(value, expected):
    assert format(value) == expected
