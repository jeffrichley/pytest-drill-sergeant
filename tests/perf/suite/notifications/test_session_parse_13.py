"""Tests for notifications session handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_session, parse

pytestmark = pytest.mark.unit


@pytest.fixture
def session():
    return make_session()


def test_parse_session_basic_0(session):
    session.label = "refund-715"

    parse(session)

    assert session.state == "held"


def test_parse_session_many_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    parse(repo, 23)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_session_single_2():
    session = make_session(amount=81, count=79)

    result = parse(session)

    assert result.total == 6399


def test_parse_session_basic_3(session):
    session.label = "refund-594"

    parse(session)

    assert session.state == "done"


def test_parse_session_many_4():
    session = make_session(amount=3, count=32)

    result = parse(session)

    assert result.total == 96
