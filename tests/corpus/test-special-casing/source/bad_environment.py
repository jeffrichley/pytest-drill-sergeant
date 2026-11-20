"""Production code that asks the environment whether a test is running.

Analysed as production code.
"""

import os as operating_system
from os import environ, getenv

if getenv("PYTEST_VERSION"):  # expect: DS403
    RETRIES = 0
else:
    RETRIES = 3


def send(message, transport):
    if operating_system.environ.get("PYTEST_CURRENT_TEST"):  # expect: DS403
        return None
    return transport.send(message, retries=RETRIES)


def log_level():
    return "ERROR" if "PYTEST_CURRENT_TEST" in environ else "INFO"  # expect: DS403


def cache_dir():
    name = environ["PYTEST_XDIST_WORKER"]  # expect: DS403
    return f"/tmp/cache-{name}"
