"""Run this checkout's drill-sergeant on another project's tests: `just try`.

`try_checks.py <path>` is `drill-sergeant check <path>`, with the project's own config.
`try_checks.py <path> DS101 DS103` also turns those checks on at `fail`, for this run
only. There is no command-line flag for that (none configure a run in v1), so this
writes a temporary config file: the pytest section the CLI's config search finds for
the path, with the checks appended to `drill_sergeant_levels`. It goes in the found
config's directory, so paths in it (source dirs, per-file ignores, `src/`, the cache)
mean what they mean in the project's own config. The run reads it through `--config`,
and it is deleted afterwards, whatever the outcome.
"""

import json
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from pytest_drill_sergeant.cli import app
from pytest_drill_sergeant.config import RawValue
from pytest_drill_sergeant.discovery import discover

LEVELS = "drill_sergeant_levels"


def _toml(value: RawValue) -> str:
    """A raw ini value as a TOML value; a JSON string is a TOML basic string."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(json.dumps(item) for item in value) + "]"
    return json.dumps(value)


def config_text(values: Mapping[str, RawValue], codes: Sequence[str]) -> str:
    """A pyproject-style config holding `values`, with each code turned on at `fail`.

    The codes are appended to `drill_sergeant_levels`, after the project's own
    entries, so they win over any entry for the same code.
    """
    existing = values.get(LEVELS, [])
    lines = existing if isinstance(existing, list) else str(existing).splitlines()
    merged = {
        **values,
        LEVELS: [
            *(line.strip() for line in lines if line.strip()),
            *(f"{code}=fail" for code in codes),
        ],
    }
    body = "".join(f"{json.dumps(key)} = {_toml(v)}\n" for key, v in merged.items())
    return f"[tool.pytest.ini_options]\n{body}"


def _check(args: list[str]) -> int:
    """Run `drill-sergeant check <args>` in this process, and return its exit code."""
    try:
        app(["check", *args], prog_name="drill-sergeant")
    except SystemExit as done:
        code = done.code
        return code if isinstance(code, int) else 0 if code is None else 1
    return 0


def main(argv: Sequence[str]) -> int:
    """Check the tests at a path, with the named checks also on; return the exit code.

    Args:
        argv: The path to check, then the codes of the checks to turn on.
    """
    if not argv:
        print("usage: try_checks.py <path> [DS### ...]", file=sys.stderr)
        return 2
    path, *codes = argv
    if not codes or not Path(path).exists():
        # Nothing to add, or nothing to check: the CLI as it stands.
        return _check([path])
    source = discover([Path(path)])
    handle, name = tempfile.mkstemp(
        prefix=".drill-sergeant-try-", suffix=".toml", dir=source.root
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            file.write(config_text(source.values, codes))
        return _check([path, "--config", name])
    finally:
        Path(name).unlink()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
