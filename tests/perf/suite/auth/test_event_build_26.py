"""Tests for auth event handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_event, build

pytestmark = pytest.mark.unit


@pytest.fixture
def event():
    return make_event()


def test_build_event_many_0(event):
    event.label = "rate-398"

    build(event)

    assert event.state == "open"


def test_build_event_large_1():
    event = make_event(amount=85, count=36)

    result = build(event)

    assert result.total == 3060


def test_build_event_many_2():
    event = make_event(amount=12, count=95)

    result = build(event)

    assert result.total == 1140


@pytest.mark.parametrize(("value", "expected"), [(6, 12), (44, 88), (1, 2)])
def test_build_event_edge_3(value, expected):
    assert build(value) == expected


def test_build_event_edge_4_runs():
    build(make_event())


def test_build_event_many_5(event):
    event.label = "token-262"

    build(event)

    assert event.state == "done"


def test_build_event_many_6():
    event = make_event(amount=20, count=54)

    result = build(event)

    assert result.total == 1080


def test_build_event_basic_7():
    event = make_event(amount=69, count=15)

    result = build(event)

    assert result.total == 1035


def test_build_event_single_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    build(repo, 183)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
