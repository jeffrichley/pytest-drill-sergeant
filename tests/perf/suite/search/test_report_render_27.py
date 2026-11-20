"""Tests for search report handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_report, render


@pytest.fixture
def report():
    return make_report()


def test_render_report_basic_0():
    report = make_report(amount=55, count=42)

    result = render(report)

    assert result.total == 2310


def test_render_report_many_1():
    report = make_report(amount=87, count=57)

    result = render(report)

    assert result.total == 4959


def test_render_report_single_2_rejects_bad_input():
    with pytest.raises(ValueError, match="report"):
        render(None)


def test_render_report_edge_3(report):
    report.label = "rate-108"

    render(report)

    assert report.state == "open"
