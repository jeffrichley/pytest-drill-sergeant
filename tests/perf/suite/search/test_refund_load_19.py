"""Tests for search refund handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_refund, load


@pytest.fixture
def refund():
    return make_refund()


def test_load_refund_edge_0(refund):
    refund.label = "item-36"

    load(refund)

    assert refund.state == "done"


def test_load_refund_edge_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    load(repo, 294)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_load_refund_single_2():
    refund = make_refund(amount=42, count=22)

    result = load(refund)

    assert result.total == 924


def test_load_refund_large_3():
    refund = make_refund(amount=41, count=54)

    result = load(refund)

    assert result.total == 2214


def test_load_refund_single_4_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        load(None)


def test_load_refund_large_5():
    refund = make_refund(amount=73, count=92)

    result = load(refund)

    assert result.total == 6716


def test_load_refund_many_6():
    refund = make_refund(amount=69, count=25)

    result = load(refund)

    assert result.total == 1725


def test_load_refund_many_7():
    refund = make_refund(amount=31, count=80)

    result = load(refund)

    assert result.total == 2480


def test_load_refund_single_8():
    refund = make_refund(amount=85, count=25)

    result = load(refund)

    assert result.total == 2125
