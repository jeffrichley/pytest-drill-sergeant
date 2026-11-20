"""Tests for orders session handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_session, split


@pytest.fixture
def session():
    return make_session()


def test_split_session_empty_0():
    session = make_session(amount=23, count=42)

    result = split(session)

    assert result.total == 966


def test_split_session_large_1(session):
    session.label = "event-239"

    split(session)

    assert session.state == "open"


def test_split_session_large_2_rejects_bad_input():
    with pytest.raises(ValueError, match="session"):
        split(None)


def test_split_session_empty_3():
    session = make_session(amount=42, count=82)

    result = split(session)

    assert result.total == 3444


def test_split_session_edge_4():
    session = make_session(amount=62, count=55)

    result = split(session)

    assert result.total == 3410


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (4, 8), (49, 98)])
def test_split_session_many_5(value, expected):
    assert split(value) == expected
