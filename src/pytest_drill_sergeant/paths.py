"""How a run writes a path: relative to a directory where it can be, or absolute.

Every place that makes a path relative (the engine to the config root, the front
ends to the directory the run started in) or absolute (the cache's keys) asks here,
so one file is written one way wherever it shows up.
"""

import os
from collections.abc import Iterator
from pathlib import Path


def relative(path: Path, base: Path) -> Path:
    """A path relative to a directory, once both are resolved, or as given outside it.

    Plain string work: pathlib's own relative-path test costs more than the rest of
    a warm run.
    """
    resolved = path.resolve().as_posix()
    prefix = base.resolve().as_posix().rstrip("/") + "/"
    return Path(resolved.removeprefix(prefix)) if resolved.startswith(prefix) else path


def absolute(path: Path) -> str:
    """A path made absolute without resolving links, as a string key."""
    return os.path.abspath(path)


def up_to(directory: str, root: str | None) -> Iterator[str]:
    """An absolute directory, then each one above it, ending at `root` if it meets it.

    Plain string work, as `absolute` writes paths; with no `root` met, it ends at
    the filesystem's root.
    """
    while True:
        yield directory
        parent = os.path.dirname(directory)
        if directory == root or parent == directory:  # noqa: PLR1714  # Two different stops.
            return
        directory = parent
