"""Tests for catalog event handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_event, parse

pytestmark = pytest.mark.unit


@pytest.fixture
def event():
    return make_event()


def test_parse_event_single_0_works():
    result = parse(make_event())
    assert result is not None


@pytest.mark.parametrize(("value", "expected"), [(16, 32), (1, 2), (44, 88)])
def test_parse_event_large_1(value, expected):
    assert parse(value) == expected


def test_parse_event_basic_2():
    event = make_event(amount=78, count=15)

    result = parse(event)

    assert result.total == 1170


@pytest.mark.parametrize(("value", "expected"), [(33, 66), (47, 94), (43, 86)])
def test_parse_event_large_3(value, expected):
    assert parse(value) == expected


def test_parse_event_empty_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    parse(repo, 285)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_event_many_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    parse(repo, 294)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
