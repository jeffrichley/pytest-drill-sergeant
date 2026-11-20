"""Tests for orders session handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_session, apply

pytestmark = pytest.mark.unit


@pytest.fixture
def session():
    return make_session()


def test_apply_session_edge_0(session):
    session.label = "report-148"

    apply(session)

    assert session.state == "done"


def test_apply_session_basic_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    apply(repo, 56)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_session_many_2():
    session = make_session(amount=5, count=7)

    result = apply(session)

    assert result.total == 35


def test_apply_session_many_3_rejects_bad_input():
    with pytest.raises(ValueError, match="session"):
        apply(None)


def test_apply_session_single_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    apply(repo, 30)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_session_single_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    apply(repo, 380)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_session_large_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    apply(repo, 191)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_session_empty_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    apply(repo, 369)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(39, 78), (21, 42), (47, 94)])
def test_apply_session_empty_8(value, expected):
    assert apply(value) == expected
