"""Tests that find a module's file through `__file__` and grep it. Analysed, never
run."""

import re
from pathlib import Path

import pytest
from app import client, settings

pytestmark = pytest.mark.unit


def test_no_todo_left():
    source = Path(client.__file__).read_text()
    assert "TODO" not in source  # expect: DS603


def test_exactly_one_handler():
    text = Path(client.__file__).read_text()
    assert len(re.findall(r"@handler", text)) == 1  # expect: DS603


def test_setting_present():
    assert re.match(r"^TIMEOUT", open(settings.__file__).read())  # expect: DS603
