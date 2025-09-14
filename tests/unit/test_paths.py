"""Tests for path utility helpers."""

from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest

from pytest_drill_sergeant.util.paths import normalize_module_path


@pytest.mark.parametrize(
    ("rel_path", "expected"),
    [
        (PurePosixPath("subdir/plugin.py"), "subdir.plugin"),
        (PureWindowsPath(r"subdir\plugin.py"), "subdir.plugin"),
        (PurePosixPath("subdir/__init__.py"), "subdir"),
        (PureWindowsPath(r"subdir\__init__.py"), "subdir"),
    ],
)
def test_normalize_module_path_cross_platform(
    tmp_path: Path, rel_path: Path, expected: str
) -> None:
    """Ensure normalize_module_path handles POSIX and Windows paths."""
    root = tmp_path
    py_file = root / rel_path
    result = normalize_module_path(py_file, root)
    assert result == expected
