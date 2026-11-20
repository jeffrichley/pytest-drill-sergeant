"""Tests for accounts event handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_event, validate


@pytest.fixture
def event():
    return make_event()


def test_validate_event_basic_0():
    event = make_event(amount=47, count=48)

    result = validate(event)

    assert result.total == 2256


def test_validate_event_many_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    validate(repo, 11)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(47, 94), (37, 74), (2, 4)])
def test_validate_event_single_2(value, expected):
    assert validate(value) == expected


def test_validate_event_empty_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    validate(repo, 443)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_event_basic_4_rejects_bad_input():
    with pytest.raises(ValueError, match="event"):
        validate(None)


def test_validate_event_empty_5(event):
    event.label = "price-275"

    validate(event)

    assert event.state == "done"


def test_validate_event_basic_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_event()

    validate(repo, 91)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(18, 36), (22, 44), (45, 90)])
def test_validate_event_many_7(value, expected):
    assert validate(value) == expected
