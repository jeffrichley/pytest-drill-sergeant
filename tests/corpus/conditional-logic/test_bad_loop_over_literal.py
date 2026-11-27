"""Loops over values the file writes out, each assertion hidden in the loop: every
one should be a `parametrize`. Two came from other checks' near-misses, and still
are: an assertion in a loop is real (DS101), and a handler that `continue`s with a
`raise` after the `try` expects the exception (DS702). Analysed, never run."""

import pytest
from quantities import parse

pytestmark = pytest.mark.unit

UNITS = ("k", "m", "b")
CASES = [
    ("1k", 1_000),
    ("2.5m", 2_500_000),
    ("3b", 3_000_000_000),
]


def test_assertion_inside_a_loop():
    for text, number in [("1", 1), ("2", 2)]:  # expect: DS107
        assert int(text) == number


def test_raise_after_the_try():
    for text in ["x", "y"]:  # expect: DS107
        try:
            parse(text)
        except ValueError:
            continue
        raise AssertionError(f"parse accepted {text!r}")


def test_parse_suffixes():
    for text, expected in CASES:  # expect: DS107
        assert parse(text) == expected


def test_every_unit_is_case_insensitive():
    for unit in UNITS:  # expect: DS107
        assert parse(f"1{unit.upper()}") == parse(f"1{unit}")


def test_rejects_garbage():
    for text in {  # expect: DS107
        "",
        "k",
        "1kk",
        "one thousand",
        "1,0000",
        "--1",
        "0x",
        "1e",
        "NaN",
    }:
        with pytest.raises(ValueError, match="quantity"):
            parse(text)


def test_law_names_every_kind(law):
    for text in ("WOMENS-LAW", "CLUB-LAW", "CREW-LAW"):  # expect: DS107
        assert text in law


def test_notes_are_out_of_character(lines):
    asked, sent, answered = lines.index("Q"), lines.index("N"), lines.index("A")
    for i in (asked, sent, answered):  # expect: DS107
        assert "out of character" in lines[i]
