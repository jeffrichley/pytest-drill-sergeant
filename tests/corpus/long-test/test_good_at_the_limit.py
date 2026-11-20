"""Near-miss: a test exactly 50 lines long, `def` to last line, is at the threshold,
not over it. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_report_summarises_a_quarter(reports):
    rows = [
        ("2026-07", "north", 1200),
        ("2026-07", "south", 900),
        ("2026-07", "east", 640),
        ("2026-07", "west", 310),
        ("2026-08", "north", 1350),
        ("2026-08", "south", 870),
        ("2026-08", "east", 700),
        ("2026-08", "west", 290),
        ("2026-09", "north", 1100),
        ("2026-09", "south", 950),
        ("2026-09", "east", 720),
        ("2026-09", "west", 330),
    ]
    targets = {
        "north": 3500,
        "south": 2700,
        "east": 2000,
        "west": 1000,
    }

    summary = reports.quarterly(
        rows,
        targets=targets,
        quarter="2026-Q3",
        currency="GBP",
    )

    assert summary.quarter == "2026-Q3"
    assert summary.totals == {
        "north": 3650,
        "south": 2720,
        "east": 2060,
        "west": 930,
    }
    assert summary.grand_total == 9360
    assert summary.over_target == ["north", "south", "east"]
    assert summary.under_target == ["west"]
    assert summary.best_month == "2026-08"
    assert summary.worst_region == "west"
    assert summary.months == ["2026-07", "2026-08", "2026-09"]
    assert summary.currency == "GBP"
    assert summary.row_count == 12
    assert summary.regions == ["east", "north", "south", "west"]
    assert summary.average_per_month == 3120
    assert summary.targets_met == 3
    assert summary.targets_missed == 1
    assert summary.best_region == "north"
    assert summary.target_total == 9200
