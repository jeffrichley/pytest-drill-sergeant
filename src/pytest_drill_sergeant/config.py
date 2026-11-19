"""The config: `drill_sergeant_*` ini options in, a typed `Config` out, no pytest.

Both front ends feed `resolve` the same raw values: the CLI from the config file it
discovers, the plugin from pytest's ini options. Every option, with its kind and
default, is listed once in `OPTIONS`.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from pytest_drill_sergeant.checks import CHECKS
from pytest_drill_sergeant.findings import Level

PREFIX = "drill_sergeant_"

# What a raw option value can be: ini files give strings, TOML and pytest's typed ini
# options also give lists, booleans and integers.
RawValue = str | bool | int | list[str]

OptionKind = Literal["string", "linelist", "bool", "int"]


class ConfigError(ValueError):
    """The config is wrong; the message names what, in one line."""


@dataclass(frozen=True)
class Config:
    """The resolved configuration the engine runs with.

    Attributes:
        mode: The run's mode: `fail` keeps each check's level, `warn` reports every
            finding as `warn`, `off` runs no check.
        levels: A level per check code, overriding the check's default.
    """

    mode: Level = Level.FAIL
    levels: Mapping[str, Level] = field(default_factory=dict)


@dataclass(frozen=True)
class Option:
    """One `drill_sergeant_*` ini option.

    Attributes:
        name: The ini key.
        kind: How its raw value is read: a string, lines, a boolean or an integer.
        default: Its value when unset, in raw form.
        help: One line on what it does.
    """

    name: str
    kind: OptionKind
    default: RawValue
    help: str


_DEFAULT = Config()

OPTIONS: tuple[Option, ...] = (
    Option(
        "drill_sergeant_mode",
        "string",
        str(_DEFAULT.mode),
        "fail, warn (report findings without failing) or off (run no check)",
    ),
    Option(
        "drill_sergeant_levels",
        "linelist",
        [],
        "CODE=level lines; a family prefix (DS1) covers the family; the most "
        "specific entry wins",
    ),
)

_OPTIONS = {option.name: option for option in OPTIONS}


def _parse_level(text: str, where: str) -> Level:
    try:
        return Level(text.strip())
    except ValueError:
        raise ConfigError(
            f"{where}: bad level {text.strip()!r}, expected fail, warn or off"
        ) from None


def _lines(name: str, value: RawValue) -> list[str]:
    if isinstance(value, list):
        lines = [str(item) for item in value]
    elif isinstance(value, str):
        lines = value.splitlines()
    else:
        raise ConfigError(f"{name}: expected lines, got {value!r}")
    return [line.strip() for line in lines if line.strip()]


def _string(name: str, value: RawValue) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"{name}: expected a string, got {value!r}")
    return value.strip()


def _family(code: str, where: str) -> str:
    """A code or family prefix (`DS101`, `DS1`, `DS1xx`) as the prefix it matches.

    Raises:
        ConfigError: When no check's code starts with it.
    """
    prefix = code.strip().rstrip("x")
    if not prefix or not any(check.code.startswith(prefix) for check in CHECKS):
        raise ConfigError(f"{where}: unknown check code {code.strip()!r}")
    return prefix


def _levels(name: str, value: RawValue) -> dict[str, Level]:
    """Each check's configured level, from `CODE=level` lines.

    The longest matching prefix wins.
    """
    by_prefix: dict[str, Level] = {}
    for line in _lines(name, value):
        code, sep, level = line.partition("=")
        if not sep:
            raise ConfigError(f"{name}: expected CODE=level, got {line!r}")
        by_prefix[_family(code, name)] = _parse_level(level, name)
    levels: dict[str, Level] = {}
    for check in CHECKS:
        matching = [p for p in by_prefix if check.code.startswith(p)]
        if matching:
            levels[check.code] = by_prefix[max(matching, key=len)]
    return levels


def resolve(raw: Mapping[str, RawValue]) -> Config:
    """Resolve raw ini values into a `Config`.

    Args:
        raw: Ini values by key. Keys without the `drill_sergeant_` prefix are
            ignored, so a whole ini section can be passed; unset options take their
            defaults.

    Returns:
        The typed config.

    Raises:
        ConfigError: On an unknown `drill_sergeant_*` key, an unknown check code, a
            bad level or a malformed value.
    """
    for key in raw:
        if key.startswith(PREFIX) and key not in _OPTIONS:
            raise ConfigError(f"unknown option {key}")
    values = {o.name: raw.get(o.name, o.default) for o in OPTIONS}
    name = "drill_sergeant_mode"
    return Config(
        mode=_parse_level(_string(name, values[name]), name),
        levels=_levels("drill_sergeant_levels", values["drill_sergeant_levels"]),
    )
