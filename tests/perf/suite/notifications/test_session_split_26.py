"""Tests for notifications session handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_session, split


@pytest.fixture
def session():
    return make_session()


def test_split_session_single_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    split(repo, 276)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_session_large_1():
    session = make_session(amount=16, count=81)

    result = split(session)

    assert result.total == 1296


def test_split_session_edge_2_rejects_bad_input():
    with pytest.raises(ValueError, match="session"):
        split(None)


def test_split_session_many_3():
    session = make_session(amount=33, count=4)

    result = split(session)

    assert result.total == 132


def test_split_session_large_4(session):
    session.label = "address-812"

    split(session)

    assert session.state == "done"


def test_split_session_basic_5():
    session = make_session(amount=1, count=78)

    result = split(session)

    assert result.total == 78
