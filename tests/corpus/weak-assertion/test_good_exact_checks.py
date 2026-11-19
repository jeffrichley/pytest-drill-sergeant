"""Near-misses: assertions that look like the weak forms but pin a value.
Analysed, never run."""

from shop import apply_discount, make_order, validate


def test_nothing_is_returned():
    assert make_order(lines=[]).coupon is None


def test_no_errors():
    errors = validate(make_order(lines=[1]))
    assert not errors


def test_exact_length():
    assert len(make_order(lines=[1, 2, 3]).lines) == 3


def test_flag_is_exactly_true():
    assert make_order(lines=[1]).paid is True


def test_predicate_call():
    assert validate.is_valid(make_order(lines=[1]))


def test_positive_total():
    assert apply_discount(make_order(lines=[1000]), pct=10).total > 0


def test_more_than_two_lines():
    assert len(make_order(lines=[1, 2, 3]).lines) > 2


def test_predicate_result_through_a_name():
    ok = validate.is_valid(make_order(lines=[1]))
    assert ok
