"""Tests for auth session handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_session, build


@pytest.fixture
def session():
    return make_session()


def test_build_session_basic_0():
    session = make_session(amount=37, count=17)

    result = build(session)

    assert result.total == 629


def test_build_session_edge_1_rejects_bad_input():
    with pytest.raises(ValueError, match="session"):
        build(None)


def test_build_session_empty_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    build(repo, 153)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_session_many_3_rejects_bad_input():
    with pytest.raises(ValueError, match="session"):
        build(None)


def test_build_session_large_4_rejects_bad_input():
    with pytest.raises(ValueError, match="session"):
        build(None)


def test_build_session_single_5(session):
    session.label = "order-307"

    build(session)

    assert session.state == "open"


def test_build_session_large_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    build(repo, 233)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
