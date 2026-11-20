"""Tests for shipping event handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_event, merge


@pytest.fixture
def event():
    return make_event()


def test_merge_event_single_0():
    event = make_event(amount=2, count=44)

    result = merge(event)

    assert result.total == 88


def test_merge_event_basic_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    merge(repo, 104)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_event_single_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    merge(repo, 113)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_event_large_3_rejects_bad_input():
    with pytest.raises(ValueError, match="event"):
        merge(None)


def test_merge_event_many_4():
    event = make_event(amount=87, count=18)

    result = merge(event)

    assert result.total == 1566


def test_merge_event_edge_5():
    event = make_event(amount=64, count=27)

    result = merge(event)

    assert result.total == 1728


def test_merge_event_empty_6():
    event = make_event(amount=43, count=45)

    result = merge(event)

    assert result.total == 1935


@pytest.mark.parametrize(("value", "expected"), [(47, 94), (8, 16), (34, 68)])
def test_merge_event_basic_7(value, expected):
    assert merge(value) == expected


def test_merge_event_single_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    merge(repo, 182)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
