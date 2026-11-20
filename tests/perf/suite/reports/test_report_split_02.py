"""Tests for reports report handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_report, split


@pytest.fixture
def report():
    return make_report()


def test_split_report_empty_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    split(repo, 364)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_report_empty_1():
    report = make_report(amount=93, count=78)

    result = split(report)

    assert result.total == 7254


def test_split_report_basic_2():
    report = make_report(amount=59, count=44)

    result = split(report)

    assert result.total == 2596


def test_split_report_single_3():
    report = make_report(amount=6, count=96)

    result = split(report)

    assert result.total == 576


@pytest.mark.parametrize(("value", "expected"), [(44, 88), (26, 52), (37, 74)])
def test_split_report_large_4(value, expected):
    assert split(value) == expected


def test_split_report_empty_5():
    report = make_report(amount=39, count=53)

    result = split(report)

    assert result.total == 2067


@pytest.mark.parametrize(("value", "expected"), [(39, 78), (42, 84), (29, 58)])
def test_split_report_large_6(value, expected):
    assert split(value) == expected
