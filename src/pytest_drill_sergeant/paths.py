"""How a run writes a path: relative to a directory where it can be, or absolute.

Every place that makes a path relative (the engine to the config root, the front
ends to the directory the run started in) or absolute (the cache's keys) asks here,
so one file is written one way wherever it shows up.
"""

import os
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
