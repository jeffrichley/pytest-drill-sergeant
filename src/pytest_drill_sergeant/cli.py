"""The `drill-sergeant` command line."""

import typer

app = typer.Typer(
    name="drill-sergeant",
    help="Catch the ways AI coding agents write bad tests.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def main() -> None:
    """Catch the ways AI coding agents write bad tests."""
