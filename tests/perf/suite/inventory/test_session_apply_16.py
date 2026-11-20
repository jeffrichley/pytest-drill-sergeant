"""Tests for inventory session handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_session, apply


@pytest.fixture
def session():
    return make_session()


@pytest.mark.parametrize(("value", "expected"), [(21, 42), (48, 96), (14, 28)])
def test_apply_session_large_0(value, expected):
    assert apply(value) == expected


def test_apply_session_edge_1_runs():
    apply(make_session())


def test_apply_session_empty_2_rejects_bad_input():
    with pytest.raises(ValueError, match="session"):
        apply(None)


def test_apply_session_basic_3():
    session = make_session(amount=49, count=50)

    result = apply(session)

    assert result.total == 2450


def test_apply_session_edge_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    apply(repo, 13)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
