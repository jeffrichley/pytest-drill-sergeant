"""Near-misses: a broad type pinned down by `match=`. Analysed, never run."""

import pytest


def parse(text):
    return int(text)


def test_broad_type_with_a_match():
    with pytest.raises(Exception, match="invalid literal"):
        parse("x")


def test_base_exception_with_a_match():
    with pytest.raises(BaseException, match="int()"):
        parse(None)


def test_broad_tuple_with_a_match():
    with pytest.raises((ValueError, Exception), match="invalid"):
        parse("x")


def test_broad_type_matched_afterwards():
    with pytest.raises(Exception) as excinfo:
        parse("x")
    assert excinfo.match("invalid literal")


def test_broad_type_matched_by_a_bare_call():
    with pytest.raises(Exception) as excinfo:
        parse("x")
    excinfo.match("invalid literal")


def test_broad_type_then_the_type_asserted():
    with pytest.raises(Exception) as excinfo:
        parse(None)
    assert excinfo.type is TypeError


def test_broad_type_then_the_message_asserted():
    with pytest.raises(Exception) as excinfo:
        parse("x")
    assert "invalid literal" in str(excinfo.value)
