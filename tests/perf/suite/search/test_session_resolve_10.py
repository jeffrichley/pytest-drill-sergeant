"""Tests for search session handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_session, resolve

pytestmark = pytest.mark.unit


@pytest.fixture
def session():
    return make_session()


def test_resolve_session_edge_0(session):
    session.label = "session-976"

    resolve(session)

    assert session.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(39, 78), (32, 64), (9, 18)])
def test_resolve_session_empty_1(value, expected):
    assert resolve(value) == expected


def test_resolve_session_edge_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    resolve(repo, 321)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_session_basic_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    resolve(repo, 355)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_session_large_4():
    session = make_session(amount=7, count=10)

    result = resolve(session)

    assert result.total == 70


def test_resolve_session_single_5_runs():
    resolve(make_session())


def test_resolve_session_empty_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    resolve(repo, 173)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_session_single_7():
    session = make_session(amount=23, count=52)

    result = resolve(session)

    assert result.total == 1196
