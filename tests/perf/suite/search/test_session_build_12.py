"""Tests for search session handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_session, build


@pytest.fixture
def session():
    return make_session()


def test_build_session_basic_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    build(repo, 108)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_session_single_1():
    session = make_session(amount=42, count=24)

    result = build(session)

    assert result.total == 1008


def test_build_session_many_2_rejects_bad_input():
    with pytest.raises(ValueError, match="session"):
        build(None)


def test_build_session_large_3_works():
    result = build(make_session())
    assert result is not None


def test_build_session_edge_4():
    session = make_session(amount=48, count=21)

    result = build(session)

    assert result.total == 1008


def test_build_session_empty_5(session):
    session.label = "user-216"

    build(session)

    assert session.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(3, 6), (22, 44), (1, 2)])
def test_build_session_basic_6(value, expected):
    assert build(value) == expected


def test_build_session_single_7():
    session = make_session(amount=97, count=12)

    result = build(session)

    assert result.total == 1164


def test_build_session_edge_8():
    session = make_session(amount=20, count=53)

    result = build(session)

    assert result.total == 1060
