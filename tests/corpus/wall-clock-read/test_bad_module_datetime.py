"""Wall-clock reads through the `datetime` module and its aliases, one of them next to
a frozen block that doesn't cover it. Analysed, never run.
"""

import datetime
import datetime as dt

import pytest
from freezegun import freeze_time
from reports import build_report

pytestmark = pytest.mark.unit


def test_report_is_dated_today():
    report = build_report()
    assert report.date == dt.date.today()  # expect: DS802


def test_report_header_has_utc_time():
    now = datetime.datetime.now(tz=datetime.UTC)  # expect: DS802
    assert build_report(at=now).header.endswith("UTC")


def test_freeze_covers_only_its_block():
    with freeze_time("2026-01-01"):
        frozen = build_report(at=datetime.datetime.now())
    assert frozen.date < datetime.date.today()  # expect: DS802
