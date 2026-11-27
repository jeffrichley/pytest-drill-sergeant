"""Branches with one path that reaches no real assertion, so the test passes on it
having checked nothing: the near-misses of test_good_every_path_asserts.py, each with
one path left bare. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_refund_with_a_bare_else(order, payments):
    result = payments.refund(order)
    if result.success:  # expect: DS107
        assert result.amount == order.total
    else:
        payments.log(result)


def test_no_else_and_nothing_asserted_after(order, payments):
    result = payments.refund(order)
    if result.success:  # expect: DS107
        assert result.amount == order.total
    print(payments.balance)


def test_line_comment_returns_with_nothing_after(parser, data):
    if parser.engine == "fast":  # expect: DS107
        with pytest.raises(ValueError, match="comment"):
            parser.read(data)
        return

    rows = parser.read(data)
    print(rows)


def test_nested_branch_with_a_bare_path(payments, order):
    result = payments.refund(order)
    if result.success:  # expect: DS107
        if result.partial:
            assert result.amount < order.total
    else:
        assert result.error_code == "card_expired"


def test_wildcard_case_that_checks_nothing(parser):
    reply = parser.parse(b"OK 3\r\n")
    match reply.kind:  # expect: DS107
        case "ok":
            assert reply.count == 3
        case _:
            parser.reset()


def test_branch_that_returns_before_it_asserts(payments, order):
    result = payments.refund(order)
    if result.success:  # expect: DS107
        print(result)
        return
    else:
        assert result.error_code == "card_expired"
    assert payments.balance == 0


def test_nested_branch_that_returns_before_the_assertion(payments, order):
    result = payments.refund(order)
    if result.success:  # expect: DS107
        if result.cached:
            return
        assert result.amount == order.total
    else:
        assert result.error_code == "card_expired"
