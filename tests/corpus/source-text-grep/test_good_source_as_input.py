"""Near-misses: source text read to feed the code under test, whose result is what
gets asserted. Analysed, never run."""

import inspect
from pathlib import Path

from app import Client, format_code, lint


def test_sample_module_lints_clean():
    source = Path("samples/clean.py").read_text()
    assert lint(source) == []


def test_formatter_reports_the_long_line():
    source = Path("samples/long_line.py").read_text()
    assert "E501" in lint(source)


def test_formatter_is_stable():
    source = inspect.getsource(Client)
    assert format_code(source) == format_code(format_code(source))
