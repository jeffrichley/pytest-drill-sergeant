"""Path utility helpers."""

from pathlib import Path


def normalize_module_path(py_file: Path, root: Path) -> str:
    """Convert a Python file path under ``root`` into a dotted module path.

    Examples:
        subdir/plugin.py     -> "subdir.plugin"
        subdir/__init__.py   -> "subdir"

    Args:
        py_file: The Python file path to convert.
        root: Root directory that ``py_file`` is relative to.

    Returns:
        Dotted module path for the Python file.
    """
    rel = py_file.relative_to(root).with_suffix("")

    if rel.name == "__init__":
        rel = rel.parent

    return ".".join(rel.parts)
