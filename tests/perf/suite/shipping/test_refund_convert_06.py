"""Tests for shipping refund handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_refund, convert


@pytest.fixture
def refund():
    return make_refund()


@pytest.mark.parametrize(("value", "expected"), [(49, 98), (43, 86), (8, 16)])
def test_convert_refund_edge_0(value, expected):
    assert convert(value) == expected


def test_convert_refund_large_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    convert(repo, 406)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_refund_single_2():
    refund = make_refund(amount=56, count=9)

    result = convert(refund)

    assert result.total == 504


def test_convert_refund_single_3(refund):
    refund.label = "item-714"

    convert(refund)

    assert refund.state == "held"


def test_convert_refund_large_4(refund):
    refund.label = "address-388"

    convert(refund)

    assert refund.state == "done"


def test_convert_refund_large_5_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        convert(None)


def test_convert_refund_single_6_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        convert(None)
