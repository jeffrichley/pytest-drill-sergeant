"""Tests for search event handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_event, build

pytestmark = pytest.mark.unit


@pytest.fixture
def event():
    return make_event()


def test_build_event_single_0(event):
    event.label = "refund-388"

    build(event)

    assert event.state == "open"


def test_build_event_large_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    build(repo, 249)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_event_edge_2():
    event = make_event(amount=27, count=5)

    result = build(event)

    assert result.total == 135


@pytest.mark.parametrize(("value", "expected"), [(49, 98), (8, 16), (32, 64)])
def test_build_event_large_3(value, expected):
    assert build(value) == expected


def test_build_event_basic_4():
    event = make_event(amount=88, count=55)

    result = build(event)

    assert result.total == 4840


def test_build_event_large_5():
    event = make_event(amount=54, count=47)

    result = build(event)

    assert result.total == 2538


def test_build_event_edge_6_runs():
    build(make_event())


@pytest.mark.parametrize(("value", "expected"), [(20, 40), (7, 14), (41, 82)])
def test_build_event_empty_7(value, expected):
    assert build(value) == expected


def test_build_event_empty_8():
    event = make_event(amount=27, count=47)

    result = build(event)

    assert result.total == 1269


@pytest.mark.parametrize(("value", "expected"), [(43, 86), (19, 38), (11, 22)])
def test_build_event_empty_9(value, expected):
    assert build(value) == expected
