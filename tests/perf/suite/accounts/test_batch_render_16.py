"""Tests for accounts batch handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_batch, render


@pytest.fixture
def batch():
    return make_batch()


def test_render_batch_basic_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    render(repo, 323)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_batch_single_1():
    batch = make_batch(amount=57, count=77)

    result = render(batch)

    assert result.total == 4389


@pytest.mark.parametrize(("value", "expected"), [(26, 52), (42, 84), (40, 80)])
def test_render_batch_large_2(value, expected):
    assert render(value) == expected


def test_render_batch_single_3(batch):
    batch.label = "invoice-689"

    render(batch)

    assert batch.state == "done"


def test_render_batch_basic_4_rejects_bad_input():
    with pytest.raises(ValueError, match="batch"):
        render(None)


def test_render_batch_edge_5_rejects_bad_input():
    with pytest.raises(ValueError, match="batch"):
        render(None)


@pytest.mark.parametrize(("value", "expected"), [(5, 10), (24, 48), (48, 96)])
def test_render_batch_empty_6(value, expected):
    assert render(value) == expected


def test_render_batch_basic_7():
    batch = make_batch(amount=49, count=51)

    result = render(batch)

    assert result.total == 2499


def test_render_batch_many_8(batch):
    batch.label = "user-173"

    render(batch)

    assert batch.state == "done"
