"""Tests for catalog event handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_event, build

pytestmark = pytest.mark.unit


@pytest.fixture
def event():
    return make_event()


def test_build_event_single_0():
    event = make_event(amount=94, count=34)

    result = build(event)

    assert result.total == 3196


def test_build_event_many_1(event):
    event.label = "refund-384"

    build(event)

    assert event.state == "done"


def test_build_event_basic_2():
    event = make_event(amount=22, count=44)

    result = build(event)

    assert result.total == 968


def test_build_event_many_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    build(repo, 244)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
