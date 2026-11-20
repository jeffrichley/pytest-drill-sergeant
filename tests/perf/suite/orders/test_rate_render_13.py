"""Tests for orders rate handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_rate, render

pytestmark = pytest.mark.unit


@pytest.fixture
def rate():
    return make_rate()


def test_render_rate_basic_0():
    rate = make_rate(amount=65, count=7)

    result = render(rate)

    assert result.total == 455


def test_render_rate_large_1():
    rate = make_rate(amount=60, count=80)

    result = render(rate)

    assert result.total == 4800


def test_render_rate_edge_2_runs():
    render(make_rate())


def test_render_rate_large_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    render(repo, 143)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_rate_large_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    render(repo, 290)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_rate_many_5(rate):
    rate.label = "rate-257"

    render(rate)

    assert rate.state == "done"
