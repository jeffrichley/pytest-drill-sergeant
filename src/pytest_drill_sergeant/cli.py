"""The `drill-sergeant` command line."""

from collections.abc import Iterator
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from pytest_drill_sergeant.config import ConfigError, resolve
from pytest_drill_sergeant.discovery import discover, load
from pytest_drill_sergeant.engine import analyze
from pytest_drill_sergeant.findings import Level
from pytest_drill_sergeant.render import render

app = typer.Typer(
    name="drill-sergeant",
    help="Catch the ways AI coding agents write bad tests.",
    no_args_is_help=True,
    add_completion=False,
)

# Directories pytest never recurses into by default (its `norecursedirs`).
_SKIPPED_DIRS = frozenset({"_darcs", "build", "CVS", "dist", "node_modules", "venv"})


# A callback makes typer treat the app as a group of subcommands (`check`, `explain`,
# `agent-guide`) rather than one command.
@app.callback()
def main() -> None:
    """Catch the ways AI coding agents write bad tests."""


def _is_test_file(path: Path) -> bool:
    return path.suffix == ".py" and (
        path.name.startswith("test_") or path.stem.endswith("_test")
    )


def _is_skipped_dir(directory: Path) -> bool:
    name = directory.name
    return name.startswith(".") or name.endswith(".egg") or name in _SKIPPED_DIRS


def _test_files(path: Path) -> Iterator[Path]:
    """The test files under a path, by pytest's default rules; a file is taken as is."""
    if path.is_file():
        yield path
        return
    for child in sorted(path.iterdir()):
        if child.is_dir():
            if not _is_skipped_dir(child):
                yield from _test_files(child)
        elif _is_test_file(child):
            yield child


def _refuse(reason: str) -> NoReturn:
    """Print one line naming what is wrong, and exit 2 as a usage error."""
    typer.echo(f"drill-sergeant: {reason}", err=True)
    raise typer.Exit(2)


@app.command()
def check(
    paths: Annotated[list[Path], typer.Argument(help="Test files or directories.")],
    config_file: Annotated[
        Path | None,
        typer.Option(
            "--config",
            help="The pytest config file to read, instead of searching upward from "
            "the paths as pytest does.",
        ),
    ] = None,
) -> None:
    """Check test files without running them; exit 1 when there are fail findings."""
    for path in paths:
        if not path.exists():
            _refuse(f"no such file or directory: {path}")
    try:
        source = load(config_file) if config_file else discover(paths)
    except ConfigError as error:
        _refuse(str(error))
    try:
        config = resolve(source.values, root=source.root)
    except ConfigError as error:
        _refuse(f"{source.path}: {error}")
    files = [file for path in paths for file in _test_files(path)]
    try:
        findings = analyze(files, config)
    except SyntaxError as error:
        _refuse(f"cannot parse {error.filename}, line {error.lineno}: {error.msg}")
    typer.echo(render(findings, voice=config.voice), nl=False)
    if any(f.level is Level.FAIL for f in findings):
        raise typer.Exit(1)
