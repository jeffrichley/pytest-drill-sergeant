"""Tests for orders event handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_event, apply


@pytest.fixture
def event():
    return make_event()


def test_apply_event_empty_0(event):
    event.label = "cart-61"

    apply(event)

    assert event.state == "open"


def test_apply_event_empty_1():
    event = make_event(amount=42, count=95)

    result = apply(event)

    assert result.total == 3990


@pytest.mark.parametrize(("value", "expected"), [(40, 80), (6, 12), (47, 94)])
def test_apply_event_empty_2(value, expected):
    assert apply(value) == expected


def test_apply_event_single_3(event):
    event.label = "cart-122"

    apply(event)

    assert event.state == "open"


def test_apply_event_basic_4(event):
    event.label = "invoice-550"

    apply(event)

    assert event.state == "held"


def test_apply_event_single_5(event):
    event.label = "refund-198"

    apply(event)

    assert event.state == "open"
