"""The `drill-sergeant` command line."""

from pathlib import Path
from typing import Annotated, NoReturn

import typer

from pytest_drill_sergeant.config import ConfigError, refusal, resolve
from pytest_drill_sergeant.discovery import discover, load, test_files
from pytest_drill_sergeant.engine import analyze
from pytest_drill_sergeant.findings import Level
from pytest_drill_sergeant.render import render

app = typer.Typer(
    name="drill-sergeant",
    help="Catch the ways AI coding agents write bad tests.",
    no_args_is_help=True,
    add_completion=False,
)


# A callback makes typer treat the app as a group of subcommands (`check`, `explain`,
# `agent-guide`) rather than one command.
@app.callback()
def main() -> None:
    """Catch the ways AI coding agents write bad tests."""


def _refuse(line: str) -> NoReturn:
    """Print one line naming what is wrong, and exit 2 as a usage error."""
    typer.echo(line, err=True)
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
            _refuse(f"drill-sergeant: no such file or directory: {path}")
    try:
        source = load(config_file) if config_file else discover(paths)
        config = resolve(source.values, root=source.root, source=source.path)
    except ConfigError as error:
        _refuse(refusal(error))
    files = test_files(paths, source)
    try:
        findings = analyze(files, config)
    except SyntaxError as error:
        _refuse(
            f"drill-sergeant: cannot parse {error.filename}, line {error.lineno}: "
            f"{error.msg}"
        )
    typer.echo(render(findings, voice=config.voice), nl=False)
    if any(f.level is Level.FAIL for f in findings):
        raise typer.Exit(1)
