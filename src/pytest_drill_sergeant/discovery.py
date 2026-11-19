"""Discovery for the CLI: the config and test files pytest would find, sans pytest.

pytest searches upward from the common ancestor of its arguments and takes the first
file, in each directory in turn, that holds a pytest section. It takes the files
matching that config's `python_files` from directories `norecursedirs` doesn't skip.
The plugin gets the same from pytest itself.
"""

import configparser
import os
import shlex
import tomllib
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

from pytest_drill_sergeant.config import ConfigError, RawValue

# pytest's defaults for the ini options that pick test files.
_PYTHON_FILES = ("test_*.py", "*_test.py")
_NORECURSEDIRS = (
    "*.egg",
    ".*",
    "_darcs",
    "build",
    "CVS",
    "dist",
    "node_modules",
    "venv",
    "{arch}",
)

# pytest's config files, in the order it tries them within one directory.
_CONFIG_NAMES = (
    "pytest.toml",
    ".pytest.toml",
    "pytest.ini",
    ".pytest.ini",
    "pyproject.toml",
    "tox.ini",
    "setup.cfg",
)


@dataclass(frozen=True)
class IniSource:
    """The ini values a run is configured with, and where they came from.

    Attributes:
        root: The directory paths in the config are relative to: the config file's,
            or the common ancestor of the checked paths when there is none.
        path: The config file, or `None` when none was found.
        values: The pytest section's values by key.
    """

    root: Path
    path: Path | None = None
    values: dict[str, RawValue] = field(default_factory=dict)


def _raw(value: object) -> RawValue:
    """A TOML value as a raw ini value."""
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str | bool | int):
        return value
    return str(value)


def _read_toml(path: Path) -> dict[str, object] | None:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ConfigError(f"{path}: cannot read it: {error}") from None
    if path.name != "pyproject.toml":
        table = data.get("pytest")
        return table if isinstance(table, dict) else {}
    tool = data.get("tool", {}).get("pytest")
    if not isinstance(tool, dict):
        return None
    ini_options = tool.get("ini_options")
    native = {k: v for k, v in tool.items() if k != "ini_options"}
    if isinstance(ini_options, dict):
        if native:
            raise ConfigError(
                f"{path}: use [tool.pytest] or [tool.pytest.ini_options], not both"
            )
        return ini_options
    return native


def _read_ini(path: Path, section: str) -> dict[str, object] | None:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str  # type: ignore[assignment,method-assign]  # Keep keys' case, as pytest does.
    try:
        parser.read_string(path.read_text(encoding="utf-8"), source=str(path))
    except (OSError, UnicodeDecodeError, configparser.Error) as error:
        raise ConfigError(f"{path}: cannot read it: {error}") from None
    if parser.has_section(section):
        return dict(parser.items(section))
    return {} if path.name in {"pytest.ini", ".pytest.ini"} else None


def _read(path: Path) -> dict[str, object] | None:
    """A config file's pytest section, or `None` when it has none."""
    if path.suffix == ".toml":
        return _read_toml(path)
    return _read_ini(path, "tool:pytest" if path.suffix == ".cfg" else "pytest")


def load(path: Path) -> IniSource:
    """The ini values in a config file named on purpose, as `--config` does.

    Raises:
        ConfigError: When the file is missing or doesn't parse.
    """
    if not path.is_file():
        raise ConfigError(f"no such config file: {path}")
    values = _read(path) or {}
    return IniSource(
        root=path.resolve().parent,
        path=path,
        values={k: _raw(v) for k, v in values.items()},
    )


def discover(paths: Iterable[Path]) -> IniSource:
    """The ini values pytest would find for these paths.

    Args:
        paths: The paths being checked; they exist.

    Returns:
        The values of the first config file with a pytest section, searching from
        the paths' common ancestor upward.

    Raises:
        ConfigError: When the config file found doesn't parse.
    """
    resolved = [path.resolve() for path in paths] or [Path.cwd()]
    ancestor = Path(os.path.commonpath(resolved))
    if ancestor.is_file():
        ancestor = ancestor.parent
    for directory in (ancestor, *ancestor.parents):
        for name in _CONFIG_NAMES:
            candidate = directory / name
            if candidate.is_file():
                values = _read(candidate)
                if values is not None:
                    return IniSource(
                        root=directory,
                        path=candidate,
                        values={k: _raw(v) for k, v in values.items()},
                    )
    return IniSource(root=ancestor)


def _patterns(source: IniSource, name: str, default: tuple[str, ...]) -> list[str]:
    """An `args` ini option's patterns, or pytest's default when it isn't set."""
    value = source.values.get(name)
    if value is None:
        return list(default)
    if isinstance(value, list):
        return value
    return shlex.split(str(value))


def _matches(path: Path, pattern: str) -> bool:
    """Whether a path matches a glob as pytest matches one.

    That is by name, or by path when
    the glob holds a `/`.
    """
    return fnmatch(path.as_posix() if "/" in pattern else path.name, pattern)


def test_files(paths: Iterable[Path], source: IniSource) -> list[Path]:
    """The test files pytest would collect from these paths, under this config.

    A file given by name is taken as is. In a directory, the `.py` files matching
    `python_files` are taken, from every subdirectory `norecursedirs` doesn't skip.
    """
    python_files = _patterns(source, "python_files", _PYTHON_FILES)
    skipped = _patterns(source, "norecursedirs", _NORECURSEDIRS)

    def walk(path: Path) -> Iterator[Path]:
        for child in sorted(path.iterdir()):
            if child.is_dir():
                if not any(_matches(child, pattern) for pattern in skipped):
                    yield from walk(child)
            elif child.suffix == ".py" and any(
                _matches(child, pattern) for pattern in python_files
            ):
                yield child

    return [
        file for path in paths for file in ([path] if path.is_file() else walk(path))
    ]
