"""CLI entry point for pytest-drill-sergeant."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import typer

from pytest_drill_sergeant.core.logging_utils import get_logger, setup_logging

app = typer.Typer(help="pytest-drill-sergeant: AI test quality enforcement")


@dataclass
class LintConfig:
    """Configuration for lint command."""

    paths: list[str]
    output_format: str = "terminal"
    output: str | None = None
    config: str | None = None
    persona: str = "drill_sergeant"
    sut_package: str | None = None
    rich_output: bool = True


def _run_lint_with_options(opts: LintConfig) -> int:
    """Execute the lint analysis with the given configuration."""
    # Set up logging based on user preference and context
    setup_logging(use_rich=opts.rich_output)
    logger = get_logger(__name__)

    logger.info("Starting analysis...")
    logger.info("Analyzing %d paths with %s persona", len(opts.paths), opts.persona)

    # TODO: Implement CLI functionality
    typer.echo(f"Analyzing {len(opts.paths)} paths with {opts.persona} persona...")
    return 0


@app.command()
def lint(  # noqa: PLR0913
    paths: Annotated[
        list[str], typer.Argument(..., help="Test files or directories to analyze")
    ],
    output_format: Annotated[
        str, typer.Option("--format", "-f", help="Output format")
    ] = "terminal",
    output: Annotated[
        str | None, typer.Option("--output", "-o", help="Output file path")
    ] = None,
    config: Annotated[
        str | None, typer.Option("--config", "-c", help="Configuration file")
    ] = None,
    persona: Annotated[
        str, typer.Option("--persona", help="Persona to use")
    ] = "drill_sergeant",
    sut_package: Annotated[
        str | None, typer.Option("--sut-package", help="SUT package name")
    ] = None,
    rich_output: Annotated[
        bool, typer.Option("--rich/--plain", help="Use rich output formatting")
    ] = True,
) -> None:
    """Analyze test files for quality issues."""
    # Create configuration and execute
    opts = LintConfig(
        paths=paths,
        output_format=output_format,
        output=output,
        config=config,
        persona=persona,
        sut_package=sut_package,
        rich_output=rich_output,
    )
    raise typer.Exit(code=_run_lint_with_options(opts))


@app.command()
def demo(
    persona: str = typer.Option("drill_sergeant", "--persona", help="Persona to use"),
    rich_output: bool = typer.Option(
        True, "--rich/--plain", help="Use rich output formatting"
    ),
) -> None:
    """Run a demo of the plugin with sample tests."""
    # Set up logging based on user preference and context
    setup_logging(use_rich=rich_output)
    logger = get_logger(__name__)

    logger.info("Running demo with %s persona", persona)

    # TODO: Implement demo functionality
    typer.echo(f"Running demo with {persona} persona...")


@app.command()
def personas(
    rich_output: bool = typer.Option(
        True, "--rich/--plain", help="Use rich output formatting"
    ),
) -> None:
    """List available personas."""
    # Set up logging based on user preference and context
    setup_logging(use_rich=rich_output)
    logger = get_logger(__name__)

    logger.info("Listing available personas")

    # TODO: Implement persona listing
    typer.echo(
        "Available personas: drill_sergeant, snoop_dogg, motivational_coach, sarcastic_butler, pirate"
    )


def cli() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    cli()
