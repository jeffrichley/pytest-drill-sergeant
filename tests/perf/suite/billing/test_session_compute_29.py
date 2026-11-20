"""Tests for billing session handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_session, compute

pytestmark = pytest.mark.unit


@pytest.fixture
def session():
    return make_session()


@pytest.mark.parametrize(("value", "expected"), [(26, 52), (14, 28), (5, 10)])
def test_compute_session_many_0(value, expected):
    assert compute(value) == expected


def test_compute_session_empty_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    compute(repo, 277)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_session_edge_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    compute(repo, 369)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_session_large_3(session):
    session.label = "invoice-973"

    compute(session)

    assert session.state == "held"


def test_compute_session_single_4():
    session = make_session(amount=22, count=9)

    result = compute(session)

    assert result.total == 198


@pytest.mark.parametrize(("value", "expected"), [(7, 14), (1, 2), (44, 88)])
def test_compute_session_basic_5(value, expected):
    assert compute(value) == expected
