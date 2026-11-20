"""Tests for notifications event handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_event, merge


@pytest.fixture
def event():
    return make_event()


def test_merge_event_empty_0():
    event = make_event(amount=7, count=66)

    result = merge(event)

    assert result.total == 462


@pytest.mark.parametrize(("value", "expected"), [(12, 24), (44, 88), (43, 86)])
def test_merge_event_single_1(value, expected):
    assert merge(value) == expected


def test_merge_event_edge_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    merge(repo, 46)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_event_large_3():
    event = make_event(amount=19, count=91)

    result = merge(event)

    assert result.total == 1729


def test_merge_event_empty_4():
    event = make_event(amount=81, count=31)

    result = merge(event)

    assert result.total == 2511
