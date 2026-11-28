"""The config: `drill_sergeant_*` ini options in, a typed `Config` out, no pytest.

Both front ends feed `resolve` the same raw values: the CLI from the config file it
discovers, the plugin from pytest's ini options. Every option, with its kind and
default, is listed once in `OPTIONS`.
"""

import shlex
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, TypeVar

from pytest_drill_sergeant.checks import CHECKS
from pytest_drill_sergeant.findings import Level

PREFIX = "drill_sergeant_"

# What a raw option value can be: ini files give strings, TOML and pytest's typed ini
# options also give lists, booleans and integers.
RawValue = str | bool | int | list[str]

# How an option's raw value is read, named as pytest's `addini` types are: `args` is
# shell-like words, `linelist` one entry per line, `int` a whole number of at least 0.
OptionKind = Literal["string", "linelist", "args", "bool", "int"]

_T = TypeVar("_T")


class ConfigError(ValueError):
    """The config is wrong; the message names what, in one line."""


def refusal(error: ConfigError) -> str:
    """The one line both front ends print when they refuse a config."""
    return f"drill-sergeant: {error}"


@dataclass(frozen=True)
class Config:
    """The resolved configuration the engine runs with.

    Attributes:
        mode: The run's mode: `fail` keeps each check's level, `warn` reports every
            finding as `warn`, `off` runs no check.
        levels: A level per check code, overriding the check's default.
        per_file_ignores: Per-file ignores, as (glob, code prefixes) pairs. A file
            whose path relative to `root` matches the glob (or whose name does, for
            a glob with no `/`) is not checked by the checks the prefixes name.
        root: The directory per-file ignore globs and source dirs are relative
            to: the config file's.
        max_file_lines: The most lines a test file may have.
        max_test_lines: The most lines of code a test function may have.
        max_mock_setup: The most mock targets a test may set up.
        max_act_assert_cycles: The most act-then-assert cycles a test may have.
        duplicate_setup_min_statements: The fewest statements a copy-pasted setup
            block has.
        duplicate_setup_min_tests: The fewest tests a copy-pasted setup block is in.
        category_markers: The category markers a test may carry.
        source_dirs: The production source directories, relative to `root`; empty
            means `src/` if it exists.
        voice: Whether findings are delivered in the voice.
        max_findings: The most findings the plugin shows; 0 means all.
        inline_waivers: Whether inline waivers are honoured.
        cache: Whether per-file results are cached.
    """

    mode: Level = Level.FAIL
    levels: Mapping[str, Level] = field(default_factory=dict)
    per_file_ignores: tuple[tuple[str, frozenset[str]], ...] = ()
    root: Path = Path()
    max_file_lines: int = 500
    max_test_lines: int = 50
    max_mock_setup: int = 5
    max_act_assert_cycles: int = 2
    duplicate_setup_min_statements: int = 3
    duplicate_setup_min_tests: int = 3
    category_markers: tuple[str, ...] = ("unit", "integration", "e2e")
    source_dirs: tuple[str, ...] = ()
    voice: bool = True
    max_findings: int = 25
    inline_waivers: bool = True
    cache: bool = True


@dataclass(frozen=True)
class Option:
    """One `drill_sergeant_*` ini option.

    Attributes:
        name: The ini key.
        kind: How its raw value is read.
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
    Option(
        "drill_sergeant_per_file_ignores",
        "linelist",
        [],
        "glob: codes lines; matching files are not checked by those checks",
    ),
    Option(
        "drill_sergeant_max_file_lines",
        "int",
        _DEFAULT.max_file_lines,
        "the most lines a test file may have",
    ),
    Option(
        "drill_sergeant_max_test_lines",
        "int",
        _DEFAULT.max_test_lines,
        "the most lines of code a test function may have",
    ),
    Option(
        "drill_sergeant_max_mock_setup",
        "int",
        _DEFAULT.max_mock_setup,
        "the most mock targets a test may set up",
    ),
    Option(
        "drill_sergeant_max_act_assert_cycles",
        "int",
        _DEFAULT.max_act_assert_cycles,
        "the most act-then-assert cycles a test may have",
    ),
    Option(
        "drill_sergeant_duplicate_setup_min_statements",
        "int",
        _DEFAULT.duplicate_setup_min_statements,
        "the fewest statements a copy-pasted setup block has",
    ),
    Option(
        "drill_sergeant_duplicate_setup_min_tests",
        "int",
        _DEFAULT.duplicate_setup_min_tests,
        "the fewest tests a copy-pasted setup block is in",
    ),
    Option(
        "drill_sergeant_category_markers",
        "args",
        list(_DEFAULT.category_markers),
        "the category markers a test may carry",
    ),
    Option(
        "drill_sergeant_source_dirs",
        "linelist",
        list(_DEFAULT.source_dirs),
        "production source directories; empty means src/ if it exists",
    ),
    Option(
        "drill_sergeant_voice",
        "bool",
        _DEFAULT.voice,
        "deliver findings in the drill-sergeant voice",
    ),
    Option(
        "drill_sergeant_max_findings",
        "int",
        _DEFAULT.max_findings,
        "the most findings the plugin shows; 0 means all",
    ),
    Option(
        "drill_sergeant_inline_waivers",
        "bool",
        _DEFAULT.inline_waivers,
        "honour inline waivers",
    ),
    Option(
        "drill_sergeant_cache",
        "bool",
        _DEFAULT.cache,
        "cache per-file results",
    ),
)

_OPTIONS = {option.name: option for option in OPTIONS}

# pytest's spellings of a boolean ini value.
_TRUE = frozenset({"y", "yes", "t", "true", "on", "1"})
_FALSE = frozenset({"n", "no", "f", "false", "off", "0"})


def _string(name: str, value: RawValue) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"{name}: expected a string, got {value!r}")
    return value.strip()


def _line_list(name: str, value: RawValue) -> list[str]:
    """A `linelist` value: one stripped entry per non-blank line."""
    if isinstance(value, list):
        lines = [str(item) for item in value]
    else:
        lines = _string(name, value).splitlines()
    return [line.strip() for line in lines if line.strip()]


def _args(name: str, value: RawValue) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return shlex.split(_string(name, value))


def _bool(name: str, value: RawValue) -> bool:
    if isinstance(value, bool):
        return value
    text = _string(name, value).lower()
    if text not in _TRUE | _FALSE:
        raise ConfigError(f"{name}: expected true or false, got {text!r}")
    return text in _TRUE


def _int(name: str, value: RawValue) -> int:
    """A whole number of at least 0."""
    if isinstance(value, bool | list):
        raise ConfigError(f"{name}: expected a whole number, got {value!r}")
    try:
        number = int(value)
    except ValueError:
        raise ConfigError(
            f"{name}: expected a whole number, got {str(value).strip()!r}"
        ) from None
    if number < 0:
        raise ConfigError(f"{name}: expected a whole number, got {number}")
    return number


def _level(name: str, text: str) -> Level:
    try:
        return Level(text.strip())
    except ValueError:
        raise ConfigError(
            f"{name}: bad level {text.strip()!r}, expected fail, warn or off"
        ) from None


def _mode(name: str, value: RawValue) -> Level:
    return _level(name, _string(name, value))


def _family(name: str, code: str) -> str:
    """A code or family prefix (`DS101`, `DS1`, `DS1xx`) as the prefix it matches.

    Raises:
        ConfigError: When no check's code starts with it.
    """
    prefix = code.strip().rstrip("x")
    if not prefix or not any(check.code.startswith(prefix) for check in CHECKS):
        raise ConfigError(f"{name}: unknown check code {code.strip()!r}")
    return prefix


def _levels(name: str, value: RawValue) -> dict[str, Level]:
    """Each check's configured level, from `CODE=level` lines.

    The longest matching prefix wins, whatever the order of the lines.
    """
    by_prefix: dict[str, Level] = {}
    for line in _line_list(name, value):
        code, sep, level = line.partition("=")
        if not sep:
            raise ConfigError(f"{name}: expected CODE=level, got {line!r}")
        by_prefix[_family(name, code)] = _level(name, level)
    levels: dict[str, Level] = {}
    for check in CHECKS:
        matching = [p for p in by_prefix if check.code.startswith(p)]
        if matching:
            levels[check.code] = by_prefix[max(matching, key=len)]
    return levels


def _per_file_ignores(
    name: str, value: RawValue
) -> tuple[tuple[str, frozenset[str]], ...]:
    """(glob, code prefixes) pairs from `glob: codes` lines.

    Codes are separated by commas or spaces.
    """
    ignores = []
    for line in _line_list(name, value):
        glob, sep, codes = line.rpartition(":")
        words = codes.replace(",", " ").split()
        if not sep or not glob.strip() or not words:
            raise ConfigError(f"{name}: expected glob: codes, got {line!r}")
        ignores.append((glob.strip(), frozenset(_family(name, c) for c in words)))
    return tuple(ignores)


def _source_dirs(name: str, value: RawValue, root: Path) -> tuple[str, ...]:
    """The production source directories, each of which must exist under `root`."""
    dirs = tuple(_line_list(name, value))
    for directory in dirs:
        if not (root / directory).is_dir():
            raise ConfigError(f"{name}: no such directory: {directory}")
    return dirs


def resolve(
    raw: Mapping[str, RawValue], root: Path = Path(), source: Path | None = None
) -> Config:
    """Resolve raw ini values into a `Config`.

    Args:
        raw: Ini values by key. Keys without the `drill_sergeant_` prefix are
            ignored, so a whole ini section can be passed; unset options take their
            defaults.
        root: The directory per-file ignore globs and source dirs are relative
            to: the config file's.
        source: The config file the values came from, named in any refusal.

    Returns:
        The typed config.

    Raises:
        ConfigError: On an unknown `drill_sergeant_*` key, an unknown check code, a
            bad level, a source dir that doesn't exist under `root`, or a malformed
            value, such as a non-numeric threshold. Its
            message starts with `source`, when there is one.
    """
    try:
        return _resolve(raw, root)
    except ConfigError as error:
        if source is None:
            raise
        raise ConfigError(f"{source}: {error}") from None


def _resolve(raw: Mapping[str, RawValue], root: Path) -> Config:
    for key in raw:
        if key.startswith(PREFIX) and key not in _OPTIONS:
            raise ConfigError(f"unknown option {key}")

    def get(parse: Callable[[str, RawValue], _T], option: str) -> _T:
        name = PREFIX + option
        return parse(name, raw.get(name, _OPTIONS[name].default))

    return Config(
        mode=get(_mode, "mode"),
        levels=get(_levels, "levels"),
        per_file_ignores=get(_per_file_ignores, "per_file_ignores"),
        root=root,
        max_file_lines=get(_int, "max_file_lines"),
        max_test_lines=get(_int, "max_test_lines"),
        max_mock_setup=get(_int, "max_mock_setup"),
        max_act_assert_cycles=get(_int, "max_act_assert_cycles"),
        duplicate_setup_min_statements=get(_int, "duplicate_setup_min_statements"),
        duplicate_setup_min_tests=get(_int, "duplicate_setup_min_tests"),
        category_markers=tuple(get(_args, "category_markers")),
        source_dirs=get(lambda n, v: _source_dirs(n, v, root), "source_dirs"),
        voice=get(_bool, "voice"),
        max_findings=get(_int, "max_findings"),
        inline_waivers=get(_bool, "inline_waivers"),
        cache=get(_bool, "cache"),
    )
