"""Tests for search session handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_session, render


@pytest.fixture
def session():
    return make_session()


def test_render_session_many_0(session):
    session.label = "invoice-329"

    render(session)

    assert session.state == "held"


def test_render_session_many_1_rejects_bad_input():
    with pytest.raises(ValueError, match="session"):
        render(None)


def test_render_session_basic_2():
    session = make_session(amount=1, count=59)

    result = render(session)

    assert result.total == 59


def test_render_session_basic_3():
    session = make_session(amount=44, count=87)

    result = render(session)

    assert result.total == 3828


def test_render_session_empty_4(session):
    session.label = "refund-729"

    render(session)

    assert session.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(38, 76), (19, 38), (5, 10)])
def test_render_session_single_5(value, expected):
    assert render(value) == expected


def test_render_session_single_6(session):
    session.label = "order-942"

    render(session)

    assert session.state == "done"


def test_render_session_edge_7_rejects_bad_input():
    with pytest.raises(ValueError, match="session"):
        render(None)


def test_render_session_edge_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_session()

    render(repo, 451)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
