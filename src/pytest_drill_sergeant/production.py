"""Which production code a run reads, and the note when there is none to read.

Both front ends ask here, so the files and the note are the same from either. The
production code is every `.py` file under `drill_sergeant_source_dirs`, or under
`src/` beside the config when that is empty, read in full every run.
"""

from dataclasses import dataclass
from pathlib import Path

from pytest_drill_sergeant.checks import CHECKS
from pytest_drill_sergeant.config import Config
from pytest_drill_sergeant.findings import Level


@dataclass(frozen=True)
class ProductionCode:
    """The production files a run reads.

    Attributes:
        files: The files, relative to the directory the run started in where they
            are under it.
        note: One line saying the checks that read production code were skipped,
            and why, or `None` when they weren't.
    """

    files: tuple[Path, ...] = ()
    note: str | None = None


def _readers(config: Config) -> list[str]:
    """The checks that read production code and will report, as `DS### name`."""
    if config.mode is Level.OFF:
        return []
    return [
        f"{check.code} {check.name}"
        for check in CHECKS
        if check.find_in_source is not None
        and config.levels.get(check.code, check.default_level) is not Level.OFF
    ]


def production_code(config: Config, here: Path) -> ProductionCode:
    """The production files to read for a run, or the note saying there are none.

    Args:
        config: The resolved config; its source dirs exist under its root.
        here: The directory the run started in.

    Returns:
        Every `.py` file under the configured source dirs, or under `src/` when
        none are configured. With neither, no files and a note naming the skipped
        checks; with no check to read them, nothing.
    """
    readers = _readers(config)
    if not readers:
        return ProductionCode()
    dirs = [config.root / d for d in config.source_dirs] or [
        d for d in [config.root / "src"] if d.is_dir()
    ]
    if not dirs:
        return ProductionCode(
            note=f"drill-sergeant: skipped {', '.join(readers)}: no src/ and no "
            "drill_sergeant_source_dirs."
        )
    here = here.resolve()
    files = sorted({f.resolve() for d in dirs for f in d.rglob("*.py")})
    return ProductionCode(
        files=tuple(f.relative_to(here) if f.is_relative_to(here) else f for f in files)
    )
