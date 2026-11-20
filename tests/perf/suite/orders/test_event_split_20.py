"""Tests for orders event handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_event, split


@pytest.fixture
def event():
    return make_event()


def test_split_event_many_0(event):
    event.label = "batch-481"

    split(event)

    assert event.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(32, 64), (26, 52), (1, 2)])
def test_split_event_many_1(value, expected):
    assert split(value) == expected


def test_split_event_empty_2(event):
    event.label = "rate-662"

    split(event)

    assert event.state == "done"


def test_split_event_single_3_rejects_bad_input():
    with pytest.raises(ValueError, match="event"):
        split(None)


def test_split_event_basic_4():
    event = make_event(amount=99, count=87)

    result = split(event)

    assert result.total == 8613
