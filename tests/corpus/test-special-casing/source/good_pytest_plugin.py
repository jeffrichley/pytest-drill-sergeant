"""Near-misses: a pytest plugin is production code that uses pytest, not code that
checks whether it is running. Analysed as production code.
"""

import sys

import pytest

HELP = "run with pytest -p myplugin"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addini("myplugin_mode", "how myplugin runs; see `pytest --help`")


def pytest_report_header() -> str:
    return f"myplugin on python {sys.version_info[0]}, see {HELP}"
