"""Tests that assert on values they wrote themselves and call nothing. Analysed,
never run."""


def test_discount_rate():  # expect: DS102
    rate = 0.1
    assert rate == 0.1  # expect: DS202


def test_arithmetic_still_works():  # expect: DS102
    assert 1 + 1 == 2  # expect: DS202


def test_status_codes():  # expect: DS102
    expected = {"ok": 200, "missing": 404}
    assert expected["ok"] == 200
    assert expected["missing"] != 200
