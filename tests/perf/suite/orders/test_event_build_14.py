"""Tests for orders event handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_event, build


@pytest.fixture
def event():
    return make_event()


@pytest.mark.parametrize(("value", "expected"), [(16, 32), (46, 92), (40, 80)])
def test_build_event_basic_0(value, expected):
    assert build(value) == expected


def test_build_event_basic_1(event):
    event.label = "session-712"

    build(event)

    assert event.state == "held"


def test_build_event_single_2(event):
    event.label = "coupon-315"

    build(event)

    assert event.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(37, 74), (16, 32), (5, 10)])
def test_build_event_many_3(value, expected):
    assert build(value) == expected


def test_build_event_large_4():
    event = make_event(amount=25, count=3)

    result = build(event)

    assert result.total == 75


def test_build_event_single_5_runs():
    build(make_event())


def test_build_event_basic_6(event):
    event.label = "refund-650"

    build(event)

    assert event.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(31, 62), (32, 64), (47, 94)])
def test_build_event_basic_7(value, expected):
    assert build(value) == expected
