"""Tests for search event handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_event, parse

pytestmark = pytest.mark.unit


@pytest.fixture
def event():
    return make_event()


def test_parse_event_edge_0():
    event = make_event(amount=71, count=99)

    result = parse(event)

    assert result.total == 7029


@pytest.mark.parametrize(("value", "expected"), [(9, 18), (30, 60), (3, 6)])
def test_parse_event_single_1(value, expected):
    assert parse(value) == expected


def test_parse_event_edge_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    parse(repo, 114)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_event_edge_3_works():
    result = parse(make_event())
    assert result is not None


def test_parse_event_large_4_rejects_bad_input():
    with pytest.raises(ValueError, match="event"):
        parse(None)


def test_parse_event_empty_5():
    event = make_event(amount=65, count=20)

    result = parse(event)

    assert result.total == 1300


def test_parse_event_large_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    parse(repo, 15)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_event_basic_7():
    event = make_event(amount=66, count=10)

    result = parse(event)

    assert result.total == 660
