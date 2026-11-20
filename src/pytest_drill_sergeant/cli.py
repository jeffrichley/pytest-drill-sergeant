"""The `drill-sergeant` command line."""

from pathlib import Path
from typing import Annotated, NoReturn

import typer
from rich.console import Console

from pytest_drill_sergeant.agent_guide import EXPLAIN_POINTER, guide, lesson, summary
from pytest_drill_sergeant.checks import CHECKS
from pytest_drill_sergeant.config import ConfigError, refusal, resolve
from pytest_drill_sergeant.discovery import cache_dir, discover, load, test_files
from pytest_drill_sergeant.engine import inspect
from pytest_drill_sergeant.findings import Level
from pytest_drill_sergeant.production import production_code
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
    show_waived: Annotated[
        bool,
        typer.Option(
            "--show-waived",
            help="List each waived finding with its waiver's reason, not only the "
            "count.",
        ),
    ] = False,
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
    production = production_code(config, Path.cwd())
    try:
        result = inspect(
            files,
            config,
            production.files,
            cache_dir=cache_dir(source) if config.cache else None,
        )
    except SyntaxError as error:
        _refuse(
            f"drill-sergeant: cannot parse {error.filename}, line {error.lineno}: "
            f"{error.msg}"
        )
    # The console reads the terminal as it is now: its width (or COLUMNS), and
    # whether it takes colour (not when piped, or under NO_COLOR).
    console = Console(highlight=False)
    console.print(
        render(
            result.findings,
            waived=result.waived,
            show_waived=show_waived,
            voice=config.voice,
            note=production.note,
        ),
        crop=False,
    )
    if any(f.level is Level.FAIL for f in result.findings):
        raise typer.Exit(1)


_CHECKS = {check.code: check for check in CHECKS}


@app.command()
def explain(
    code: Annotated[
        str | None,
        typer.Argument(help="A check's code, such as DS101; none lists every check."),
    ] = None,
) -> None:
    """Teach a check: why it matters, a test it flags and the fixed test."""
    if code is None:
        typer.echo(f"{summary()}\n\n{EXPLAIN_POINTER}")
        return
    check = _CHECKS.get(code)
    if check is None:
        _refuse(
            f"drill-sergeant: no check {code}; `drill-sergeant explain` lists them."
        )
    typer.echo(lesson(check))


@app.command("agent-guide")
def agent_guide() -> None:
    """Print the agent guide, which teaches a coding agent the checks."""
    typer.echo(guide())
