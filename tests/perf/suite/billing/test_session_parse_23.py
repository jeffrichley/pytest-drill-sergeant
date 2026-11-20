"""Tests for billing session handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_session, parse


@pytest.fixture
def session():
    return make_session()


@pytest.mark.parametrize(("value", "expected"), [(38, 76), (49, 98), (24, 48)])
def test_parse_session_empty_0(value, expected):
    assert parse(value) == expected


def test_parse_session_empty_1(session):
    session.label = "rate-280"

    parse(session)

    assert session.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(10, 20), (47, 94), (25, 50)])
def test_parse_session_edge_2(value, expected):
    assert parse(value) == expected


def test_parse_session_large_3_rejects_bad_input():
    with pytest.raises(ValueError, match="session"):
        parse(None)


@pytest.mark.parametrize(("value", "expected"), [(44, 88), (17, 34), (47, 94)])
def test_parse_session_single_4(value, expected):
    assert parse(value) == expected
