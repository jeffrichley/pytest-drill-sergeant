"""Rendered `repr`, `str` and `format` output compared with `==`. Analysed, never
run."""

import pytest
from app import Money, Report, User

pytestmark = pytest.mark.unit


def test_user_repr():
    user = User(name="Ada", email="ada@example.com")
    assert (  # expect: DS601
        repr(user) == "<User name='Ada' email='ada@example.com' active=True>"
    )


def test_report_str():
    report = Report(passed=3, failed=1)
    assert str(report) == "3 passed, 1 failed in 0.12s"  # expect: DS601


def test_money_format():
    assert (  # expect: DS601
        format(Money(1234), "long") == "one thousand two hundred thirty four dollars"
    )


def test_lowered_str_compared_with_not_equal():
    report = Report(passed=0, failed=0)
    assert str(report).lower() != "no tests ran at all"  # expect: DS601
