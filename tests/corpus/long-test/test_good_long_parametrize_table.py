"""Near-miss: a long `parametrize` table is the test's data, in its decorator; the
test itself is short. Analysed, never run."""

import pytest
from quantities import parse_quantity

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0", 0),
        ("1", 1),
        ("-1", -1),
        ("+1", 1),
        ("007", 7),
        ("1_000", 1000),
        ("1,000", 1000),
        ("1 000", 1000),
        ("1e3", 1000),
        ("1E3", 1000),
        ("2.5k", 2500),
        ("2.5K", 2500),
        ("3m", 3_000_000),
        ("3M", 3_000_000),
        ("1b", 1_000_000_000),
        ("0x10", 16),
        ("0o10", 8),
        ("0b10", 2),
        ("  42  ", 42),
        ("\t42\n", 42),
        ("forty-two", None),
        ("", None),
        ("-", None),
        ("+", None),
        ("1.5.2", None),
        ("k", None),
        ("1kk", None),
        ("0x", None),
        ("0xZZ", None),
        ("1__000", None),
        ("_1000", None),
        ("1000_", None),
        ("1,00", None),
        ("1,0000", None),
        ("١٢٣", 123),
        ("１２３", 123),
        ("-0", 0),
        ("+0", 0),
        ("00", 0),
        ("9" * 20, 99_999_999_999_999_999_999),
        ("-9" * 1, -9),
        ("12abc", None),
        ("abc12", None),
        ("1 2", None),
        ("1\n2", None),
        ("nan", None),
        ("inf", None),
        ("-inf", None),
        ("None", None),
        ("null", None),
        ("true", None),
        ("false", None),
    ],
)
def test_parse_quantity(raw, expected):
    assert parse_quantity(raw) == expected
