"""Tests that pull source with `inspect` and grep it. Analysed, never run."""

import inspect
import re
from inspect import getsource

import pytest
from app import Client, jobs

pytestmark = pytest.mark.unit


def test_no_sleep_in_fetch():
    assert "time.sleep" not in inspect.getsource(Client.fetch)  # expect: DS603


def test_v2_handlers_defined():
    source = getsource(jobs)
    assert re.search(r"def \w+_v2", source)  # expect: DS603


def test_lines_mention_cache():
    lines, _ = inspect.getsourcelines(Client)
    assert any("cache" in line for line in lines)  # expect: DS603
