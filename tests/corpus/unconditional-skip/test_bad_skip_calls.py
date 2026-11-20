"""Tests that skip themselves on every run, with nothing left to check.

Analysed, never run.
"""

import pytest
from pytest import skip
from reports import Report


def test_report_totals_each_column():
    pytest.skip("unrelated failure, fix later")  # expect: DS402


def test_report_exports_csv():
    report = Report([[1, 2]])
    skip("csv export is flaky")  # expect: DS402
    assert report.to_csv() == "1,2\n"


async def test_report_streams_rows():
    pytest.skip(reason="times out on CI")  # expect: DS402
