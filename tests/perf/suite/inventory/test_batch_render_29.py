"""Tests for inventory batch handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_batch, render

pytestmark = pytest.mark.unit


@pytest.fixture
def batch():
    return make_batch()


def test_render_batch_large_0():
    batch = make_batch(amount=91, count=54)

    result = render(batch)

    assert result.total == 4914


def test_render_batch_edge_1(batch):
    batch.label = "report-736"

    render(batch)

    assert batch.state == "done"


def test_render_batch_single_2_runs():
    render(make_batch())


def test_render_batch_large_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    render(repo, 335)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_batch_empty_4(batch):
    batch.label = "order-790"

    render(batch)

    assert batch.state == "done"


def test_render_batch_single_5():
    batch = make_batch(amount=94, count=49)

    result = render(batch)

    assert result.total == 4606


def test_render_batch_edge_6():
    batch = make_batch(amount=36, count=51)

    result = render(batch)

    assert result.total == 1836


def test_render_batch_single_7():
    batch = make_batch(amount=79, count=27)

    result = render(batch)

    assert result.total == 2133
