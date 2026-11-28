"""`isinstance` against a builtin the file doesn't rebind: almost any value of that
type passes, wrong ones included. Analysed, never run."""

import pytest
from shop import load_settings, parse_amount

pytestmark = pytest.mark.unit


def test_settings_load_as_a_dict():
    settings = load_settings("shop.toml")
    assert isinstance(settings, dict)  # expect: DS201


def test_amount_parses_as_a_number():
    amount = parse_amount("10.50")
    assert isinstance(amount, (int, float))  # expect: DS201


def test_names_from_a_comprehension_without_a_filter():
    settings = load_settings("shop.toml")
    names = [key for key in settings]
    assert names  # expect: DS201
