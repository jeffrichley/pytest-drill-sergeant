"""Tests for auth session handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_session, apply

pytestmark = pytest.mark.unit


@pytest.fixture
def session():
    return make_session()


@pytest.mark.parametrize(("value", "expected"), [(3, 6), (46, 92), (22, 44)])
def test_apply_session_many_0(value, expected):
    assert apply(value) == expected


def test_apply_session_basic_1():
    session = make_session(amount=33, count=65)

    result = apply(session)

    assert result.total == 2145


def test_apply_session_large_2():
    session = make_session(amount=21, count=10)

    result = apply(session)

    assert result.total == 210


def test_apply_session_edge_3():
    session = make_session(amount=89, count=32)

    result = apply(session)

    assert result.total == 2848


def test_apply_session_many_4():
    session = make_session(amount=69, count=78)

    result = apply(session)

    assert result.total == 5382


def test_apply_session_edge_5():
    session = make_session(amount=19, count=1)

    result = apply(session)

    assert result.total == 19


def test_apply_session_many_6():
    session = make_session(amount=19, count=30)

    result = apply(session)

    assert result.total == 570


def test_apply_session_edge_7():
    session = make_session(amount=49, count=26)

    result = apply(session)

    assert result.total == 1274


def test_apply_session_large_8():
    session = make_session(amount=81, count=86)

    result = apply(session)

    assert result.total == 6966
