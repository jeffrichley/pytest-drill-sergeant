"""Near-misses: the same probes asked about something other than pytest.

Analysed as production code.
"""

import os
import sys


def has_numpy():
    return "numpy" in sys.modules


def home():
    return os.environ.get("HOME", "/")


def program():
    return os.path.basename(sys.argv[0])


def debug():
    return os.getenv("APP_DEBUG") == "1"
