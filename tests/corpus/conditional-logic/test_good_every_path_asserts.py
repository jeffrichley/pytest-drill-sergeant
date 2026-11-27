"""Near-misses: branches where every path reaches a real assertion, so no path passes
unchecked. Modelled on httpx's `test_proxies_environ` (an `if`/`else` that asserts
on both sides) and pandas's `test_line_comment` (branches that expect an error and
`return`, with the assertion after the `if`); and pandas's `test_intersection_equal`,
an `if` with no `else` that falls through to an assertion after it. Analysed, never
run."""

import pytest
from shop import parse_csv, read_proxy

pytestmark = pytest.mark.unit


def _assert_refused(result, code):
    assert result.error_code == code


def test_refund(order, payments):
    result = payments.refund(order)
    if result.success:
        assert result.amount == order.total
    else:
        assert result.error_code == "card_expired"


def test_proxy_from_the_environment(client, url, expected):
    transport = read_proxy(client, url)

    if expected is None:
        assert transport == client.default
    elif expected == "direct":
        assert transport.direct is True
    else:
        assert transport.proxy_url == expected


def test_line_comment(engine, data):
    if engine == "fast":
        with pytest.raises(ValueError, match="comment"):
            parse_csv(data, engine=engine)
        return
    elif engine == "slow":
        raise AssertionError("the slow engine never takes comments")

    result = parse_csv(data, engine=engine)
    assert result == [[1, 2], [5, 10]]


def test_refusal_checked_in_a_helper(order, payments):
    result = payments.refund(order)
    if result.success:
        assert result.amount == order.total
    else:
        _assert_refused(result, "card_expired")


def test_parse_reply_with_a_wildcard(parser):
    reply = parser.parse(b"OK 3\r\n")
    match reply.kind:
        case "ok":
            assert reply.count == 3
        case _:
            pytest.fail(reply.message)


def test_nested_branches_that_all_assert(payments, order):
    result = payments.refund(order)
    if result.success:
        if result.partial:
            assert result.amount < order.total
        else:
            assert result.amount == order.total
    else:
        assert result.error_code == "card_expired"


def test_paths_that_assert_through_a_repeat_and_a_try(payments, order):
    result = payments.refund(order)
    if result.success:
        for _ in range(2):
            assert payments.refund(order).duplicate is True
    else:
        try:
            payments.retry(order)
        finally:
            assert payments.balance == 0


def test_no_else_with_an_assertion_after_the_if(order, payments):
    result = payments.refund(order)
    if result.success:
        assert result.amount == order.total
    assert payments.balance == 0


def test_retry_until_it_works(client):
    response = client.get("/health")
    if response.status_code != 200:
        response = client.get("/health")
        if response.status_code != 200:
            raise AssertionError(response.text)
    assert response.json() == {"status": "up"}


def test_match_with_no_wildcard_and_an_assertion_after(parser):
    reply = parser.parse(b"OK 3\r\n")
    match reply.kind:
        case "ok":
            assert reply.count == 3
    assert reply.raw == b"OK 3\r\n"


def test_nested_no_else_falls_through_to_the_outer_assertion(payments, order):
    result = payments.refund(order)
    if result.success:
        if result.partial:
            assert result.amount < order.total
    else:
        assert result.error_code == "card_expired"
    assert payments.balance == 0
