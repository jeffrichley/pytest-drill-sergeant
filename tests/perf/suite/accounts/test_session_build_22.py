"""Tests for accounts session handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_session, build


@pytest.fixture
def session():
    return make_session()


def test_build_session_many_0():
    session = make_session(amount=95, count=61)

    result = build(session)

    assert result.total == 5795


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (3, 6), (26, 52)])
def test_build_session_basic_1(value, expected):
    assert build(value) == expected


def test_build_session_single_2(session):
    session.label = "report-394"

    build(session)

    assert session.state == "open"


def test_build_session_many_3():
    session = make_session(amount=21, count=70)

    result = build(session)

    assert result.total == 1470


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (19, 38), (32, 64)])
def test_build_session_many_4(value, expected):
    assert build(value) == expected
