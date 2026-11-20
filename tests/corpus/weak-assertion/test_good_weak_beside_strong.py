"""Near-misses: weak assertions that guard a strong one. Seeded from the archived
rewrite's test_tiny_coverage.py, which pinned the version beside its weak checks.
Analysed, never run."""

from unittest import mock

import pytest
from shop import Sender, apply_discount, make_order, notify

import pytest_drill_sergeant

pytestmark = pytest.mark.unit


def test_tiny_coverage_boost():
    assert pytest_drill_sergeant.__version__ == "1.0.0-dev"
    assert pytest_drill_sergeant.__doc__ is not None
    assert len(str(pytest_drill_sergeant.__version__)) > 0


def test_total_after_a_guard():
    order = apply_discount(make_order(lines=[1000, 1000]), pct=10)
    assert order is not None
    assert order.total == 1800


def test_weak_check_beside_mock_verification():
    sender = mock.Mock(spec=Sender)
    result = notify(sender, "hi")
    assert result
    sender.send.assert_called_once_with("hi")


def test_weak_check_beside_an_expected_error():
    assert isinstance(make_order(lines=[]), object)
    with pytest.raises(ValueError, match="no lines"):
        apply_discount(make_order(lines=[]), pct=10)
