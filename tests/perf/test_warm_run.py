"""The speed budget: a warm run with nothing changed adds at most about 50 ms per
300 test files. The test fails only past twice that, so a slow CI machine passes and
a real slowdown doesn't.

The suite in `suite/` is committed, never generated at run time: 300 small test
files of the everyday kinds, a few with the slips drill-sergeant reports. It is
analysed, never run.
"""

import statistics
import time
from pathlib import Path

import pytest

from pytest_drill_sergeant.engine import Config, inspect

SUITE = Path(__file__).parent / "suite"

# Seconds a warm run with nothing changed may add per test file: 50 ms per 300.
BUDGET_PER_FILE = 0.050 / 300


@pytest.mark.perf
def test_warm_run_with_nothing_changed_stays_within_twice_the_budget(cache_dir):
    files = sorted(SUITE.rglob("test_*.py"))
    inspect(files, Config(), cache_dir=cache_dir)
    times = []
    for _ in range(5):
        start = time.perf_counter()
        inspect(files, Config(), cache_dir=cache_dir)
        times.append(time.perf_counter() - start)

    assert len(files) == 300
    assert statistics.median(times) <= 2 * BUDGET_PER_FILE * len(files)
