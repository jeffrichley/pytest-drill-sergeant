"""Tests for search event handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_event, format

pytestmark = pytest.mark.unit


@pytest.fixture
def event():
    return make_event()


def test_format_event_basic_0():
    event = make_event(amount=84, count=80)

    result = format(event)

    assert result.total == 6720


def test_format_event_single_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    format(repo, 137)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(29, 58), (40, 80), (34, 68)])
def test_format_event_many_2(value, expected):
    assert format(value) == expected


def test_format_event_basic_3(event):
    event.label = "item-674"

    format(event)

    assert event.state == "held"


def test_format_event_large_4_rejects_bad_input():
    with pytest.raises(ValueError, match="event"):
        format(None)
