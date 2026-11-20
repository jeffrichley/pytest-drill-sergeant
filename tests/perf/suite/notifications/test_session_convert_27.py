"""Tests for notifications session handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_session, convert


@pytest.fixture
def session():
    return make_session()


def test_convert_session_single_0():
    session = make_session(amount=22, count=17)

    result = convert(session)

    assert result.total == 374


def test_convert_session_single_1_works():
    result = convert(make_session())
    assert result is not None


def test_convert_session_single_2():
    session = make_session(amount=30, count=25)

    result = convert(session)

    assert result.total == 750


def test_convert_session_large_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    convert(repo, 404)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_session_many_4():
    session = make_session(amount=96, count=65)

    result = convert(session)

    assert result.total == 6240
