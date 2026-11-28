"""The project's declared dependencies: the packages its files name, sans pytest.

A test file's project declares what the files in its directory, and in each directory
above it up to the config root, name as dependencies:

- `pyproject.toml`: `[project]`'s `dependencies` and `optional-dependencies`,
  `[dependency-groups]`, `[tool.uv]`'s `dev-dependencies`, and Poetry's
  `[tool.poetry.dependencies]`, `[tool.poetry.dev-dependencies]` and
  `[tool.poetry.group.<name>.dependencies]`;
- every `requirements*.txt`, and every `.txt` in a `requirements/` directory: one
  requirement per line, comments, blank lines and option lines (`-r`, `--index-url`)
  aside.

Those are the directories an import from the file is looked for in, so the plugin
and the CLI, which hand the engine the same config root, read the same files. Each
name is normalised as PEP 503 does (`Pytest_Mock` is `pytest-mock`). A file that
can't be read or parsed declares nothing.
"""

import os
import re
import tomllib
from collections.abc import Iterable, Iterator
from pathlib import Path

from pytest_drill_sergeant.paths import absolute, up_to

_PYPROJECT = "pyproject.toml"
_REQUIREMENTS = re.compile(r"requirements.*\.txt")
_REQUIREMENTS_DIR = "requirements"

# A requirement's name, at the start of a PEP 508 string or a requirements line.
_NAME = re.compile(r"\s*([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)")


def normalised(name: str) -> str:
    """A package name as PEP 503 normalises it."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement(text: str) -> str | None:
    """The package a PEP 508 requirement names, normalised, if it names one."""
    match = _NAME.match(text)
    return normalised(match.group(1)) if match else None


def _strings(value: object) -> Iterator[str]:
    """The strings in a TOML list; anything else, such as an include, is skipped."""
    if isinstance(value, list):
        yield from (item for item in value if isinstance(item, str))


def _tables(value: object) -> Iterator[object]:
    """The values of a TOML table, or nothing when it isn't one."""
    if isinstance(value, dict):
        yield from value.values()


def _table(data: object, *keys: str) -> object:
    """The value under a path of keys in nested TOML tables, or `None`."""
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def _pyproject(path: Path) -> Iterator[str]:
    """The requirements a `pyproject.toml` declares, as PEP 508 strings or names."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return
    yield from _strings(_table(data, "project", "dependencies"))
    for extra in _tables(_table(data, "project", "optional-dependencies")):
        yield from _strings(extra)
    for group in _tables(data.get("dependency-groups")):
        yield from _strings(group)
    yield from _strings(_table(data, "tool", "uv", "dev-dependencies"))
    poetry = _table(data, "tool", "poetry")
    for table in (
        _table(poetry, "dependencies"),
        _table(poetry, "dev-dependencies"),
        *(_table(g, "dependencies") for g in _tables(_table(poetry, "group"))),
    ):
        if isinstance(table, dict):
            yield from table


def _requirements_file(path: Path) -> Iterator[str]:
    """The requirements a requirements file declares, one per line."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return
    for line in lines:
        text = line.strip()
        if text and not text.startswith(("#", "-")):
            yield text


def _requirements_files(directory: Path) -> Iterable[Path]:
    """A directory's requirements files, and those in its `requirements/`."""
    try:
        beside = [p for p in directory.iterdir() if _REQUIREMENTS.fullmatch(p.name)]
    except OSError:
        return []
    nested = directory / _REQUIREMENTS_DIR
    below = sorted(nested.glob("*.txt")) if nested.is_dir() else []
    return [*sorted(beside), *below]


def _declared_in(directory: Path) -> frozenset[str]:
    """The packages the files in one directory declare."""
    requirements = [*_pyproject(directory / _PYPROJECT)]
    for path in _requirements_files(directory):
        requirements.extend(_requirements_file(path))
    return frozenset(
        name for text in requirements if (name := _requirement(text)) is not None
    )


class Dependencies:
    """What a run's projects declare, each directory read at most once per run."""

    def __init__(self, root: Path) -> None:
        """The declarations of the project under a config root."""
        self._root = absolute(root)
        self._by_directory: dict[str, frozenset[str]] = {}

    def declared(self, path: Path) -> frozenset[str]:
        """The packages a test file's project declares, normalised.

        Read from its directory and each directory above it, up to the config root
        when it is under it.
        """
        start = os.path.dirname(absolute(path))
        return frozenset().union(*map(self._in, up_to(start, self._root)))

    def _in(self, directory: str) -> frozenset[str]:
        known = self._by_directory.get(directory)
        if known is None:
            known = self._by_directory[directory] = _declared_in(Path(directory))
        return known
