"""Near-misses: a name bound from the code, then changed by the code before the
assertion, or a call compared to a value worked out by hand.
Analysed, never run."""

import pytest
from shop import Counter, gross_price, snapshot

pytestmark = pytest.mark.unit


def test_value_read_before_a_change():
    counter = Counter()
    before = counter.value()
    counter.increment()
    assert counter.value() == before + 1


def test_value_unchanged_by_a_read_only_call():
    counter = Counter()
    before = counter.value()
    counter.peek()
    assert counter.value() == before


def test_value_changed_by_setting_an_attribute(cart):
    before = cart.total()
    cart.discount = 10
    assert cart.total() == before


def test_value_changed_by_an_augmented_assignment(counter):
    first = counter.value()
    counter.n += 1
    assert counter.value() == first


def test_result_passed_to_code_before_the_check():
    result = gross_price(100, 20)
    Counter().record(result)
    assert result == 120


def test_expected_worked_out_by_hand():
    expected = 120
    assert gross_price(100, 20) == expected


def test_snapshot_unchanged_by_a_checked_call(cart):
    before = snapshot(cart)
    assert cart.apply("SAVE10") is False
    assert snapshot(cart) == before
