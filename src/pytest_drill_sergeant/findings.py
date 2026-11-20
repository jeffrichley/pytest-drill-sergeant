"""What a check reports: a finding, and the level it is reported at."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Level(StrEnum):
    """How a check's findings count: they fail the run, warn, or are not reported."""

    FAIL = "fail"
    WARN = "warn"
    OFF = "off"


@dataclass(frozen=True)
class Finding:
    """One occurrence of a failure mode in a specific test, or in a whole test file.

    Attributes:
        code: The check's permanent `DS###` code.
        name: The check's kebab-case name.
        file: The test file, as it was given to the engine.
        line: The line the finding is reported on.
        test: The test's name, with its class path (`TestX::test_y`), or empty for
            a finding about the whole file (a file too long).
        level: The level the finding is reported at.
        found: What the check found, in plain words.
        why: Why that matters.
        fix: How to fix it, naming the specifics where the check knows them.
    """

    code: str
    name: str
    file: Path
    line: int
    test: str
    level: Level
    found: str
    why: str
    fix: str
