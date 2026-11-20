"""Tests for orders session handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_session, build

pytestmark = pytest.mark.unit


@pytest.fixture
def session():
    return make_session()


def test_build_session_many_0():
    session = make_session(amount=3, count=51)

    result = build(session)

    assert result.total == 153


def test_build_session_many_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    build(repo, 267)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_session_edge_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    build(repo, 146)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(20, 40), (16, 32), (3, 6)])
def test_build_session_basic_3(value, expected):
    assert build(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(12, 24), (26, 52), (34, 68)])
def test_build_session_many_4(value, expected):
    assert build(value) == expected


def test_build_session_many_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    build(repo, 26)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(31, 62), (47, 94), (23, 46)])
def test_build_session_single_6(value, expected):
    assert build(value) == expected
