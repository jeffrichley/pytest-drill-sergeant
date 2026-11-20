"""Tests for search report handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_report, split


@pytest.fixture
def report():
    return make_report()


def test_split_report_single_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    split(repo, 403)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(42, 84), (7, 14), (23, 46)])
def test_split_report_basic_1(value, expected):
    assert split(value) == expected


def test_split_report_edge_2():
    report = make_report(amount=29, count=66)

    result = split(report)

    assert result.total == 1914


def test_split_report_empty_3():
    report = make_report(amount=33, count=8)

    result = split(report)

    assert result.total == 264


def test_split_report_many_4():
    report = make_report(amount=38, count=21)

    result = split(report)

    assert result.total == 798


@pytest.mark.parametrize(("value", "expected"), [(33, 66), (21, 42), (19, 38)])
def test_split_report_basic_5(value, expected):
    assert split(value) == expected
