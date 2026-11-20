"""Tests for orders session handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_session, validate

pytestmark = pytest.mark.unit


@pytest.fixture
def session():
    return make_session()


def test_validate_session_single_0():
    session = make_session(amount=81, count=66)

    result = validate(session)

    assert result.total == 5346


def test_validate_session_single_1():
    session = make_session(amount=21, count=88)

    result = validate(session)

    assert result.total == 1848


def test_validate_session_single_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    validate(repo, 101)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_session_single_3():
    session = make_session(amount=4, count=46)

    result = validate(session)

    assert result.total == 184


def test_validate_session_basic_4(session):
    session.label = "user-940"

    validate(session)

    assert session.state == "open"


def test_validate_session_large_5(session):
    session.label = "batch-723"

    validate(session)

    assert session.state == "open"
