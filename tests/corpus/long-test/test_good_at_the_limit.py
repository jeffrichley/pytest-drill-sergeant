"""Near-miss: a test with exactly 50 lines of code, `def` to last line, is at the
threshold, not over it. Its blank lines and comments don't count. Analysed, never
run."""

import pytest

pytestmark = pytest.mark.unit


def test_report_summarises_a_quarter(reports):
    # Arrange: three months of sales for four regions.
    report = reports.new(quarter="2026-Q3", currency="GBP")
    report.add_row("2026-07", "north", 1200)
    report.add_row("2026-07", "south", 900)
    report.add_row("2026-07", "east", 640)
    report.add_row("2026-07", "west", 310)
    report.add_row("2026-08", "north", 1350)
    report.add_row("2026-08", "south", 870)
    report.add_row("2026-08", "east", 700)
    report.add_row("2026-08", "west", 290)
    report.add_row("2026-09", "north", 1100)
    report.add_row("2026-09", "south", 950)
    report.add_row("2026-09", "east", 720)
    report.add_row("2026-09", "west", 330)
    report.set_target("north", 3500)
    report.set_target("south", 2700)
    report.set_target("east", 2000)
    report.set_target("west", 1000)

    # Act
    summary = report.summarise()

    # Assert
    assert summary.quarter == "2026-Q3"
    assert summary.totals["north"] == 3650
    assert summary.totals["south"] == 2720
    assert summary.totals["east"] == 2060
    assert summary.totals["west"] == 930
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
    assert summary.worst_month == "2026-07"
    assert summary.growth["north"] == -8
    assert summary.growth["south"] == 6
    assert summary.growth["east"] == 9
    assert summary.growth["west"] == 6
    assert summary.share["north"] == 39
    assert summary.share["south"] == 29
    assert summary.share["east"] == 22
    assert summary.share["west"] == 10
    assert summary.shortfall["west"] == 70
    assert summary.surplus["north"] == 150
    assert summary.rows_per_region == 3
