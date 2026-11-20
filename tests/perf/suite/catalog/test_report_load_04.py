"""Tests for catalog report handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_report, load


@pytest.fixture
def report():
    return make_report()


@pytest.mark.parametrize(("value", "expected"), [(13, 26), (48, 96), (46, 92)])
def test_load_report_empty_0(value, expected):
    assert load(value) == expected


def test_load_report_empty_1():
    report = make_report(amount=4, count=40)

    result = load(report)

    assert result.total == 160


def test_load_report_empty_2():
    report = make_report(amount=53, count=75)

    result = load(report)

    assert result.total == 3975


def test_load_report_single_3(report):
    report.label = "item-217"

    load(report)

    assert report.state == "held"


def test_load_report_single_4():
    report = make_report(amount=29, count=45)

    result = load(report)

    assert result.total == 1305


def test_load_report_basic_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    load(repo, 308)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_load_report_many_6_works():
    result = load(make_report())
    assert result is not None


def test_load_report_large_7():
    report = make_report(amount=41, count=25)

    result = load(report)

    assert result.total == 1025
