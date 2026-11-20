"""Tests for accounts session handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_session, resolve

pytestmark = pytest.mark.unit


@pytest.fixture
def session():
    return make_session()


def test_resolve_session_edge_0():
    session = make_session(amount=91, count=19)

    result = resolve(session)

    assert result.total == 1729


def test_resolve_session_large_1(session):
    session.label = "batch-83"

    resolve(session)

    assert session.state == "open"


def test_resolve_session_edge_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    resolve(repo, 436)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(35, 70), (15, 30), (7, 14)])
def test_resolve_session_large_3(value, expected):
    assert resolve(value) == expected


def test_resolve_session_single_4(session):
    session.label = "item-718"

    resolve(session)

    assert session.state == "held"
