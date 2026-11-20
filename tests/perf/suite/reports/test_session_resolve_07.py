"""Tests for reports session handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_session, resolve

pytestmark = pytest.mark.unit


@pytest.fixture
def session():
    return make_session()


@pytest.mark.parametrize(("value", "expected"), [(20, 40), (41, 82), (28, 56)])
def test_resolve_session_large_0(value, expected):
    assert resolve(value) == expected


def test_resolve_session_single_1():
    session = make_session(amount=45, count=25)

    result = resolve(session)

    assert result.total == 1125


def test_resolve_session_empty_2():
    session = make_session(amount=68, count=90)

    result = resolve(session)

    assert result.total == 6120


def test_resolve_session_large_3():
    session = make_session(amount=9, count=73)

    result = resolve(session)

    assert result.total == 657


def test_resolve_session_empty_4_works():
    result = resolve(make_session())
    assert result is not None


def test_resolve_session_many_5(session):
    session.label = "session-204"

    resolve(session)

    assert session.state == "done"


def test_resolve_session_large_6():
    session = make_session(amount=99, count=55)

    result = resolve(session)

    assert result.total == 5445


def test_resolve_session_empty_7(session):
    session.label = "batch-810"

    resolve(session)

    assert session.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(17, 34), (18, 36), (24, 48)])
def test_resolve_session_edge_8(value, expected):
    assert resolve(value) == expected
