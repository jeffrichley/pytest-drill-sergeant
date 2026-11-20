"""Near-miss: the call after the guard assertion is a helper imported from another
module of the test tree that asserts, as pandas' `_check_colors` is, so it is an
assertion, not an act. Analysed, never run."""

import pytest
from plot_checks import check_colors

pytestmark = pytest.mark.unit


def test_guard_then_an_imported_helper_that_asserts(plot):
    assert plot.patches
    check_colors(plot.patches, ["red", "blue"])
