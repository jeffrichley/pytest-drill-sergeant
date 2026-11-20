"""Tests for search report handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_report, validate

pytestmark = pytest.mark.unit


@pytest.fixture
def report():
    return make_report()


def test_validate_report_basic_0():
    report = make_report(amount=49, count=42)

    result = validate(report)

    assert result.total == 2058


@pytest.mark.parametrize(("value", "expected"), [(14, 28), (29, 58), (40, 80)])
def test_validate_report_many_1(value, expected):
    assert validate(value) == expected


def test_validate_report_many_2():
    report = make_report(amount=93, count=92)

    result = validate(report)

    assert result.total == 8556


def test_validate_report_empty_3():
    report = make_report(amount=52, count=1)

    result = validate(report)

    assert result.total == 52


def test_validate_report_basic_4():
    report = make_report(amount=1, count=76)

    result = validate(report)

    assert result.total == 76


def test_validate_report_basic_5_rejects_bad_input():
    with pytest.raises(ValueError, match="report"):
        validate(None)


def test_validate_report_basic_6():
    report = make_report(amount=96, count=11)

    result = validate(report)

    assert result.total == 1056


def test_validate_report_edge_7():
    report = make_report(amount=57, count=76)

    result = validate(report)

    assert result.total == 4332
