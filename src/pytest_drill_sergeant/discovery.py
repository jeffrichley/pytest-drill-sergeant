"""Config discovery for the CLI: find the config file pytest would, without pytest.

pytest searches upward from the common ancestor of its arguments and takes the first
file, in each directory in turn, that holds a pytest section. The plugin gets the
same values from pytest itself.
"""

import configparser
import os
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from pytest_drill_sergeant.config import ConfigError, RawValue

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
