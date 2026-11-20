"""Tests for reports event handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_event, apply

pytestmark = pytest.mark.unit


@pytest.fixture
def event():
    return make_event()


def test_apply_event_large_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    apply(repo, 449)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_event_large_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    apply(repo, 148)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_event_many_2(event):
    event.label = "cart-327"

    apply(event)

    assert event.state == "done"


def test_apply_event_many_3(event):
    event.label = "event-845"

    apply(event)

    assert event.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(36, 72), (6, 12), (2, 4)])
def test_apply_event_large_4(value, expected):
    assert apply(value) == expected


def test_apply_event_empty_5(event):
    event.label = "item-452"

    apply(event)

    assert event.state == "held"


def test_apply_event_empty_6(event):
    event.label = "user-270"

    apply(event)

    assert event.state == "held"
