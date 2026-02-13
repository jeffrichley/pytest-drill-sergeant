"""Pytest Drill Sergeant - Enforce test quality standards.

A pytest plugin that enforces test quality standards by:
- Auto-detecting test markers based on directory structure
- Enforcing AAA (Arrange-Act-Assert) structure with descriptive comments
- Providing comprehensive error reporting for violations
"""

__version__ = "0.3.1"
__author__ = "Jeff Richley"
__email__ = "jeffrichley@gmail.com"

# Import main plugin functionality
from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.models import ValidationIssue
from pytest_drill_sergeant.plugin import pytest_runtest_setup
from pytest_drill_sergeant.pytest_options import pytest_addoption
from pytest_drill_sergeant.validators import (
    AAAValidator,
    ErrorReporter,
    MarkerValidator,
)

__all__ = [
    "AAAValidator",
    "DrillSergeantConfig",
    "ErrorReporter",
    "MarkerValidator",
    "ValidationIssue",
    "__author__",
    "__email__",
    "__version__",
    "pytest_addoption",
    "pytest_runtest_setup",
]
