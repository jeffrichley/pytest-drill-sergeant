"""Tests for orders event handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_event, validate

pytestmark = pytest.mark.unit


@pytest.fixture
def event():
    return make_event()


def test_validate_event_many_0_runs():
    validate(make_event())


def test_validate_event_basic_1():
    event = make_event(amount=26, count=76)

    result = validate(event)

    assert result.total == 1976


def test_validate_event_empty_2():
    event = make_event(amount=82, count=62)

    result = validate(event)

    assert result.total == 5084


def test_validate_event_basic_3():
    event = make_event(amount=85, count=35)

    result = validate(event)

    assert result.total == 2975


def test_validate_event_basic_4():
    event = make_event(amount=23, count=50)

    result = validate(event)

    assert result.total == 1150


def test_validate_event_basic_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    validate(repo, 460)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_event_large_6(event):
    event.label = "batch-274"

    validate(event)

    assert event.state == "done"


def test_validate_event_edge_7():
    event = make_event(amount=62, count=1)

    result = validate(event)

    assert result.total == 62


@pytest.mark.parametrize(("value", "expected"), [(29, 58), (24, 48), (35, 70)])
def test_validate_event_empty_8(value, expected):
    assert validate(value) == expected


def test_validate_event_empty_9(event):
    event.label = "price-287"

    validate(event)

    assert event.state == "held"
