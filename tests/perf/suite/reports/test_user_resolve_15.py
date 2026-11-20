"""Tests for reports user handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_user, resolve


@pytest.fixture
def user():
    return make_user()


def test_resolve_user_empty_0(user):
    user.label = "order-305"

    resolve(user)

    assert user.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(9, 18), (39, 78), (28, 56)])
def test_resolve_user_edge_1(value, expected):
    assert resolve(value) == expected


def test_resolve_user_large_2(user):
    user.label = "report-969"

    resolve(user)

    assert user.state == "open"


def test_resolve_user_edge_3(user):
    user.label = "user-403"

    resolve(user)

    assert user.state == "open"


def test_resolve_user_basic_4_rejects_bad_input():
    with pytest.raises(ValueError, match="user"):
        resolve(None)


def test_resolve_user_large_5_rejects_bad_input():
    with pytest.raises(ValueError, match="user"):
        resolve(None)
