"""The `drill-sergeant` command line."""

from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

import typer

from pytest_drill_sergeant.engine import Config, analyze
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


def _skipped(directory: Path) -> bool:
    name = directory.name
    return name.startswith(".") or name.endswith(".egg") or name in _SKIPPED_DIRS


def _test_files(path: Path) -> Iterator[Path]:
    """The test files under a path, by pytest's default rules; a file is taken as is."""
    if path.is_file():
        yield path
        return
    for child in sorted(path.iterdir()):
        if child.is_dir():
            if not _skipped(child):
                yield from _test_files(child)
        elif _is_test_file(child):
            yield child


@app.command()
def check(
    paths: Annotated[
        list[Path], typer.Argument(help="Test files or directories.", exists=True)
    ],
) -> None:
    """Check test files without running them; exit 1 when there are findings."""
    files = [file for path in paths for file in _test_files(path)]
    try:
        findings = analyze(files, Config())
    except SyntaxError as error:
        typer.echo(
            f"drill-sergeant: cannot parse {error.filename}, line {error.lineno}: "
            f"{error.msg}",
            err=True,
        )
        raise typer.Exit(2) from error
    typer.echo(render(findings), nl=False)
    if any(f.level is Level.FAIL for f in findings):
        raise typer.Exit(1)
