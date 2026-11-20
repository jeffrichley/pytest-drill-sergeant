"""Tests for inventory session handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_session, parse


@pytest.fixture
def session():
    return make_session()


def test_parse_session_empty_0(session):
    session.label = "refund-952"

    parse(session)

    assert session.state == "done"


def test_parse_session_edge_1(session):
    session.label = "session-447"

    parse(session)

    assert session.state == "done"


def test_parse_session_single_2_rejects_bad_input():
    with pytest.raises(ValueError, match="session"):
        parse(None)


def test_parse_session_many_3():
    session = make_session(amount=33, count=12)

    result = parse(session)

    assert result.total == 396


@pytest.mark.parametrize(("value", "expected"), [(2, 4), (32, 64), (24, 48)])
def test_parse_session_many_4(value, expected):
    assert parse(value) == expected


def test_parse_session_basic_5():
    session = make_session(amount=68, count=12)

    result = parse(session)

    assert result.total == 816


@pytest.mark.parametrize(("value", "expected"), [(6, 12), (46, 92), (39, 78)])
def test_parse_session_single_6(value, expected):
    assert parse(value) == expected


def test_parse_session_many_7():
    session = make_session(amount=32, count=77)

    result = parse(session)

    assert result.total == 2464


@pytest.mark.parametrize(("value", "expected"), [(7, 14), (47, 94), (36, 72)])
def test_parse_session_edge_8(value, expected):
    assert parse(value) == expected
