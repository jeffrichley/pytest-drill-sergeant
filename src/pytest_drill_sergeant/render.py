"""The renderer: findings in, the drill sergeant's report out, as Rich renderables.

The report is built from `Text` objects, never markup, so the brackets and backticks
in a finding's text are printed as they stand. The caller prints it through a
`rich.console.Console` that knows the terminal: its width, and whether it takes
colour and hyperlinks.
"""

import hashlib
from collections import Counter
from collections.abc import Iterable, Sequence
from itertools import groupby
from pathlib import Path

from rich.console import Console, ConsoleOptions, Group, RenderableType, RenderResult
from rich.segment import Segment
from rich.style import Style
from rich.text import Text

from pytest_drill_sergeant.checks import CHECKS
from pytest_drill_sergeant.findings import Finding, Level
from pytest_drill_sergeant.waivers import WaivedFinding

_VOICE = {check.code: check.voice for check in CHECKS}

_LEVEL_STYLE = {Level.FAIL: "bold red", Level.WARN: "bold yellow"}
_BANNER = "bold red"
_FILE = "bold underline"
_VOICE_STYLE = "italic magenta"
_LABEL = "bold"

# How far a finding sits under its file, and its voice line and facts under it.
_FINDING_INDENT = 2
_FACT_INDENT = 4


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _voice_line(finding: Finding) -> str:
    """The check's voice line for this finding.

    It's picked by a stable hash of (check, file, test), so the same finding always
    gets the same line.
    """
    lines = _VOICE[finding.code]
    key = f"{finding.code}|{finding.file.as_posix()}|{finding.test}".encode()
    return lines[int.from_bytes(hashlib.sha256(key).digest()[:8], "big") % len(lines)]


class _Unwrapped:
    """One line of text that is never wrapped or cropped, however narrow the terminal.

    A finding's location stays whole, so a terminal or editor can still follow it; a
    line wider than the terminal is left for the terminal to fold. Print it with
    `crop=False`.
    """

    def __init__(self, text: Text) -> None:
        self.text = text

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from self.text.render(console)
        yield Segment.line()


class _Hanging:
    """Rows in two columns: a head, then a body that wraps under itself.

    The body wraps to the console's width, each wrapped line under the body, not
    under the head. Every body starts at the same column, just past the widest head.
    """

    def __init__(self, rows: list[tuple[Text, Text]]) -> None:
        self.rows = rows

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        column = max(head.cell_len for head, _ in self.rows)
        width = max(options.max_width - column, 1)
        for head, body in self.rows:
            for row, line in enumerate(body.wrap(console, width, overflow="fold")):
                line.rstrip()
                lead = head.copy() if row == 0 else Text()
                lead.pad_right(column - lead.cell_len)
                yield from (lead + line).render(console)
                yield Segment.line()


def _facts(finding: Finding) -> _Hanging:
    """Found/Why/Fix: bold labels, then the plain text."""
    rows = [("Found:", finding.found), ("Why:", finding.why), ("Fix:", finding.fix)]
    return _Hanging(
        [
            (Text.assemble(" " * _FACT_INDENT, (label, _LABEL), " "), Text(fact))
            for label, fact in rows
        ]
    )


def _voice(finding: Finding) -> _Hanging:
    """The voice line, in quotes, wrapping inside them."""
    return _Hanging(
        [
            (
                Text(f'{" " * _FACT_INDENT}"', _VOICE_STYLE),
                Text(f'{_voice_line(finding)}"', _VOICE_STYLE),
            )
        ]
    )


def _location(finding: Finding) -> Text:
    """The finding's header line: where it is, which check, its level and its test.

    `path:line` links to the file, for a terminal that follows hyperlinks.
    """
    path = finding.file.as_posix()
    text = Text(" " * _FINDING_INDENT)
    text.append(
        f"{path}:{finding.line}", Style(link=Path(finding.file).resolve().as_uri())
    )
    text.append(": ")
    text.append(finding.code, "bold")
    text.append(" ")
    text.append(finding.name, "dim")
    text.append(" ")
    text.append(f"[{finding.level}]", _LEVEL_STYLE.get(finding.level, ""))
    text.append(" in ")
    text.append(finding.test, "bold")
    return text


def _finding(finding: Finding, *, voice: bool) -> Iterable[RenderableType]:
    yield _Unwrapped(_location(finding))
    if voice:
        yield _voice(finding)
    yield _facts(finding)


def _waived_finding(waived: WaivedFinding) -> Iterable[RenderableType]:
    yield _Unwrapped(_location(waived.finding))
    yield _Hanging(
        [
            (
                Text.assemble(" " * _FACT_INDENT, ("Reason:", _LABEL), " "),
                Text(waived.reason),
            )
        ]
    )


def _tally(findings: list[Finding], waived: int, *, voice: bool) -> Text:
    levels = Counter(f.level for f in findings)
    text = Text(f"{_plural(len(findings), 'finding')}: ", "bold")
    text.append(f"{levels[Level.FAIL]} fail", _LEVEL_STYLE[Level.FAIL])
    text.append(", ")
    text.append(f"{levels[Level.WARN]} warn", _LEVEL_STYLE[Level.WARN])
    text.append(f"; {waived} waived.")
    if voice:
        text.append(" Fix them, recruit. DISMISSED!", _BANNER)
    return text


def _all_clear(waived: int, *, voice: bool) -> Text:
    if voice:
        return Text(
            f"DRILL SERGEANT INSPECTION: no findings, {waived} waived. As you were!",
            _BANNER,
        )
    return Text(f"No findings, {waived} waived.")


def render(
    findings: list[Finding],
    *,
    waived: Sequence[WaivedFinding] = (),
    show_waived: bool = False,
    voice: bool = True,
    max_findings: int = 0,
) -> RenderableType:
    """Render findings as the report.

    The report is a banner, the findings grouped by file and findings by line, each
    with one voice line and plain Found/Why/Fix, and a closing tally by level, with
    the number of waived findings, and a flourish. With `max_findings`, only the
    first that many findings are shown, then a line counting the rest; the banner
    and tally still count every finding. With `show_waived`, each waived finding is
    listed with its waiver's reason before the tally. With the voice off there is
    no banner, voice line or flourish; the Found/Why/Fix lines are unchanged.

    A finding's location line is never wrapped; its Found/Why/Fix wrap to the
    console's width, each wrapped line under the text it continues. Print the report
    with `crop=False`.

    Args:
        findings: The findings to report, in the engine's order (by file, line and
            code), which keeps each file's findings together.
        waived: The findings inline waivers silenced, in the engine's order.
        show_waived: Whether to list the waived findings, not only count them.
        voice: Whether to deliver the report in the voice.
        max_findings: The most findings to show; 0 shows them all.

    Returns:
        The report, ready for `Console.print`.
    """
    out: list[RenderableType] = []
    if findings:
        files = len({f.file for f in findings})
        if voice:
            out += [
                Text(
                    f"DRILL SERGEANT INSPECTION: {_plural(len(findings), 'finding')} "
                    f"in {_plural(files, 'file')}. FALL IN!",
                    _BANNER,
                ),
                Text(),
            ]
        shown = findings[:max_findings] if max_findings else findings
        for file, group in groupby(shown, key=lambda f: f.file.as_posix()):
            out.append(Text(file, _FILE))
            for f in group:
                out += _finding(f, voice=voice)
            out.append(Text())
        if len(shown) < len(findings):
            cap = Text(f"…and {len(findings) - len(shown)} more, run ", "bold")
            cap.append("`drill-sergeant check`", "bold cyan")
            cap.append(" for all", "bold")
            out += [cap, Text()]
    if show_waived and waived:
        out.append(Text("Waived findings", _FILE))
        for w in waived:
            out += _waived_finding(w)
        out.append(Text())
    out.append(
        _tally(findings, len(waived), voice=voice)
        if findings
        else _all_clear(len(waived), voice=voice)
    )
    return Group(*out)
