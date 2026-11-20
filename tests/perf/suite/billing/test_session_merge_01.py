"""Tests for billing session handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_session, merge


@pytest.fixture
def session():
    return make_session()


def test_merge_session_basic_0_rejects_bad_input():
    with pytest.raises(ValueError, match="session"):
        merge(None)


def test_merge_session_single_1():
    session = make_session(amount=88, count=23)

    result = merge(session)

    assert result.total == 2024


def test_merge_session_single_2(session):
    session.label = "item-73"

    merge(session)

    assert session.state == "done"


def test_merge_session_empty_3():
    session = make_session(amount=77, count=36)

    result = merge(session)

    assert result.total == 2772


def test_merge_session_edge_4(session):
    session.label = "invoice-744"

    merge(session)

    assert session.state == "held"


def test_merge_session_large_5(session):
    session.label = "token-892"

    merge(session)

    assert session.state == "held"


def test_merge_session_single_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    merge(repo, 380)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
