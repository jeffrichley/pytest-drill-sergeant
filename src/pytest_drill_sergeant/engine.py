"""The engine: test files, production code and a config in, findings out.

No pytest in sight.
"""

import ast
import dataclasses
import gc
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path, PurePath

from pytest_drill_sergeant.cache import Cache, content_hash, context
from pytest_drill_sergeant.checks import (
    CHECKS,
    Check,
    Hit,
    SourceFile,
    TestFile,
    TestFunction,
)
from pytest_drill_sergeant.checks.ast_tools import (
    FIXTURE_DECORATORS,
    TEST_PATH,
    imports_seen_by,
    inside,
    module_imports,
    qualified,
)
from pytest_drill_sergeant.checks.base import (
    FileSummary,
    FunctionNode,
    Thresholds,
)
from pytest_drill_sergeant.checks.summary import summarize
from pytest_drill_sergeant.config import Config
from pytest_drill_sergeant.findings import MODULE, Finding, Level
from pytest_drill_sergeant.paths import relative
from pytest_drill_sergeant.tokens import read
from pytest_drill_sergeant.waivers import (
    FileWaivers,
    WaivedFinding,
    apply,
    parse,
)

__all__ = ["Config", "Inspection", "UnreadableFileError", "analyze", "inspect"]


class UnreadableFileError(Exception):
    """A file the run was given can't be read; the message names it, in one line.

    The message is the one line both front ends print when they refuse.
    """


def _require_source(path: Path) -> bytes:
    """A file's bytes.

    Raises:
        UnreadableFileError: When reading it fails in any way, gone since it was
            found or otherwise.
    """
    try:
        return path.read_bytes()
    except OSError as error:
        reason = error.strerror or type(error).__name__
        raise UnreadableFileError(
            f"drill-sergeant: cannot read {path}: {reason}"
        ) from None


def _is_fixture(node: FunctionNode, names: Mapping[str, str]) -> bool:
    """Whether a function is a pytest fixture, which pytest never collects as a test.

    Its decorator is `pytest.fixture` (or `pytest_asyncio.fixture`), called or not,
    through whatever name the imports give it.
    """
    return any(
        qualified(d.func if isinstance(d, ast.Call) else d, names) in FIXTURE_DECORATORS
        for d in node.decorator_list
    )


def _is_collected_class(node: ast.ClassDef) -> bool:
    """Whether pytest collects a class.

    It does when the class is named `Test*`, has no `__init__` and isn't opted out
    with `__test__ = False`.
    """
    if not node.name.startswith("Test"):
        return False
    for statement in node.body:
        if isinstance(statement, ast.FunctionDef) and statement.name == "__init__":
            return False
        if (
            isinstance(statement, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "__test__"
                for t in statement.targets
            )
            and isinstance(statement.value, ast.Constant)
            and not statement.value.value
        ):
            return False
    return True


def _tests_in(
    body: list[ast.stmt],
    names: Mapping[str, str],
    where: str = MODULE,
    classes: tuple[ast.ClassDef, ...] = (),
) -> Iterator[TestFunction]:
    """The tests pytest's default rules collect.

    Those are `test*` functions that aren't fixtures, at module level or in the
    classes pytest collects, nested ones included.
    """
    for node in body:
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name.startswith("test")
            and not _is_fixture(node, names)
        ):
            yield TestFunction(
                name=inside(where, node.name, TEST_PATH),
                node=node,
                imports=imports_seen_by(node, names),
                classes=classes,
            )
        elif isinstance(node, ast.ClassDef) and _is_collected_class(node):
            yield from _tests_in(
                node.body, names, inside(where, node.name, TEST_PATH), (*classes, node)
            )


def _directories(path: PurePath) -> tuple[str, ...]:
    """The names of the directories a path runs through, outermost first."""
    parts = path.parent.parts
    return parts[1:] if path.anchor else parts


def _ignored_codes(path: Path, config: Config) -> frozenset[str]:
    """The code prefixes the config's per-file ignores turn off for a file.

    A glob matches the file's path relative to the config root, or, for a glob with
    no `/`, the file's name.
    """
    if not config.per_file_ignores:
        return frozenset()
    within = relative(path, config.root).as_posix()
    ignored: set[str] = set()
    for glob, codes in config.per_file_ignores:
        if fnmatch(within, glob) or ("/" not in glob and fnmatch(path.name, glob)):
            ignored |= codes
    return frozenset(ignored)


@dataclass(frozen=True)
class Inspection:
    """What one run over the test files and production code found.

    Attributes:
        findings: The findings that stand, ordered by file, line and code.
        waived: The findings an inline waiver silenced, in the same order.
    """

    findings: list[Finding]
    waived: list[WaivedFinding]


def _thresholds(config: Config) -> Thresholds:
    return Thresholds(
        max_file_lines=config.max_file_lines,
        max_test_lines=config.max_test_lines,
        max_mock_setup=config.max_mock_setup,
        duplicate_setup_min_statements=config.duplicate_setup_min_statements,
        duplicate_setup_min_tests=config.duplicate_setup_min_tests,
    )


def _level(check: Check, ignored: frozenset[str], config: Config) -> Level:
    """The level a check reports at in a file, `off` if it doesn't report there."""
    level = config.levels.get(check.code, check.default_level)
    if level is Level.OFF or any(check.code.startswith(c) for c in ignored):
        return Level.OFF
    return Level.WARN if config.mode is Level.WARN else level


def _finding(check: Check, path: Path, hit: Hit, level: Level) -> Finding:
    return Finding(
        code=check.code,
        name=check.name,
        file=path,
        line=hit.line,
        test=hit.test,
        level=level,
        found=hit.found,
        why=check.why,
        fix=hit.fix,
    )


@dataclass(frozen=True)
class _FileResult:
    """What per-file analysis gives for one file, before the config's levels apply.

    It is what the cache keeps, so it holds every check's hits, whatever its level:
    a changed level or per-file ignore never needs a file analysed again.

    Attributes:
        hits: Each check's hits in the file, by the check's code; a check with
            none is left out.
        summary: The file's per-file summary.
        waivers: The file's inline waivers, for applying after cross-file analysis.
    """

    hits: Mapping[str, tuple[Hit, ...]]
    summary: FileSummary
    waivers: FileWaivers


# The config fields per-file analysis never reads: changing one of them keeps every
# cached result. Every other field is part of the cache key, so a field added to
# the config invalidates the cache until it is listed here.
# The root stays in: DS901's fix names a directory of the file's path below it.
_NOT_PER_FILE = frozenset(
    {"mode", "levels", "per_file_ignores", "voice", "max_findings", "cache"}
)


def _per_file_settings(config: Config) -> dict[str, object]:
    """The config fields that can change a file's per-file result."""
    return {
        f.name: getattr(config, f.name)
        for f in dataclasses.fields(config)
        if f.name not in _NOT_PER_FILE
    }


def _analyze_file(path: Path, source: bytes, config: Config) -> _FileResult:
    """Per-file analysis: every check's hits in a file, its summary and waivers."""
    module = ast.parse(source, filename=str(path))
    tests = tuple(_tests_in(module.body, module_imports(module)))
    tokens = read(source)
    waivers = parse(tokens.comments) if config.inline_waivers else ()
    file = TestFile(
        path=path,
        module=module,
        tests=tests,
        lines=len(source.splitlines()),
        waivers=waivers,
        thresholds=_thresholds(config),
        category_markers=config.category_markers,
        directories=_directories(relative(path, config.root)),
        comments=tokens.comments,
    )
    return _FileResult(
        hits={c.code: hits for c in CHECKS if (hits := tuple(c.find(file)))},
        summary=summarize(file),
        waivers=FileWaivers(
            waivers=waivers,
            def_lines={
                t.name: (
                    t.node.lineno,
                    tokens.signature_ends.get(t.node.lineno, t.node.lineno),
                )
                for t in tests
            },
        ),
    )


def _file_result(
    path: Path, config: Config, cache: Cache | None, shared: str
) -> _FileResult:
    """A file's per-file result: from the cache when its key still matches."""
    source = _require_source(path)
    if cache is None:
        return _analyze_file(path, source, config)
    key = f"{content_hash(source)}:{shared}"
    result = cache.get(path, key, _FileResult)
    if result is None:
        result = _analyze_file(path, source, config)
        cache.put(path, key, result)
    return result


# The level each check reports at in a file, by the check's code.
Levels = Mapping[str, Level]


def _levels_by_file(paths: list[Path], config: Config) -> dict[Path, Levels]:
    """The level each check reports at in each file.

    Files that the same per-file ignores match share one mapping.
    """
    shared: dict[frozenset[str], Levels] = {}
    by_file: dict[Path, Levels] = {}
    for path in paths:
        ignored = _ignored_codes(path, config)
        if ignored not in shared:
            shared[ignored] = {c.code: _level(c, ignored, config) for c in CHECKS}
        by_file[path] = shared[ignored]
    return by_file


def _file_findings(path: Path, result: _FileResult, levels: Levels) -> list[Finding]:
    """A file's findings: its hits, at the level each check reports at there.

    A check that yields to a more specific one drops its hits on the tests that
    check reports on here.
    """

    def taken(check: Check) -> set[str]:
        other = check.yields_to
        if other is None or levels[other] is Level.OFF:
            return set()
        return {hit.test for hit in result.hits.get(other, ())}

    return [
        _finding(check, path, hit, levels[check.code])
        for check in CHECKS
        if levels[check.code] is not Level.OFF
        for yielded in [taken(check)]
        for hit in result.hits.get(check.code, ())
        if hit.test not in yielded
    ]


def _analyze_source(
    path: Path, config: Config, levels: Levels
) -> tuple[list[Finding], FileWaivers]:
    """A production file's findings and its inline waivers.

    The findings are those of the checks that read production code; a waiver
    silences a finding on its own line.
    """
    source = _require_source(path)
    file = SourceFile(path=path, module=ast.parse(source, filename=str(path)))
    findings = [
        _finding(check, path, hit, levels[check.code])
        for check in CHECKS
        if check.find_in_source is not None and levels[check.code] is not Level.OFF
        for hit in check.find_in_source(file)
    ]
    waivers = parse(read(source).comments) if config.inline_waivers else ()
    return findings, FileWaivers(waivers=waivers, def_lines={})


def _compare_files(
    summaries: list[tuple[Path, FileSummary]],
    levels: Mapping[Path, Levels],
    config: Config,
) -> list[Finding]:
    """Cross-file analysis: the findings comparing every file's summary turns up.

    A file a per-file ignore keeps a check off is left out of that check's
    comparison.
    """

    def reports(code: str, path: Path) -> bool:
        return levels[path][code] is not Level.OFF

    findings: list[Finding] = []
    for check in CHECKS:
        if check.find_across is None:
            continue
        code = check.code
        seen = [(p, s) for p, s in summaries if levels[p][code] is not Level.OFF]
        findings.extend(
            _finding(check, path, hit, levels[path][code])
            for path, hit in check.find_across(seen, _thresholds(config), reports)
        )
    return findings


def analyze(
    paths: Iterable[Path],
    config: Config,
    sources: Iterable[Path] = (),
    *,
    cache_dir: Path | None = None,
) -> list[Finding]:
    """Run every check over the test files and production code; return what stands.

    The same as `inspect(paths, config, sources, cache_dir=cache_dir).findings`.
    """
    return inspect(paths, config, sources, cache_dir=cache_dir).findings


def inspect(
    paths: Iterable[Path],
    config: Config,
    sources: Iterable[Path] = (),
    *,
    cache_dir: Path | None = None,
) -> Inspection:
    """Run every check over the test files and production code, then apply waivers.

    Each file is analysed on its own, for its findings and its per-file summary;
    then the summaries, never the files, are compared across files. The
    production files are read in full, by the checks that read production code
    (DS403) and no others.

    Args:
        paths: The test files to analyse.
        config: The resolved configuration.
        sources: The production files to analyse. They are never cached: they are
            read in full every run.
        cache_dir: The directory the cache is kept in, or `None` to run uncached.
            With `config.cache` off the run is uncached too. A test file whose
            bytes, drill-sergeant and per-file settings are unchanged since a
            cached run isn't analysed again; cross-file analysis always reruns,
            from the summaries.

    Returns:
        The findings that stand and the waived ones, each ordered by file, line
        and code. Checks configured `off` report none, nor do checks a per-file
        ignore names for a file, and none run in `off` mode; in `warn` mode every
        finding is reported as `warn`. With inline waivers off, no finding is
        waived and malformed waivers (DS001) aren't reported.

    Raises:
        UnreadableFileError: When a test or production file can't be read.
    """
    findings: list[Finding] = []
    files: dict[Path, FileWaivers] = {}
    if config.mode is Level.OFF:
        return Inspection(findings=findings, waived=[])
    # The run makes tens of thousands of small objects, all freed by reference
    # count; the cycle collector would only walk them, at a quarter of a warm run.
    with _cycle_collector_paused():
        cache = Cache(cache_dir) if cache_dir is not None and config.cache else None
        shared = context(_per_file_settings(config)) if cache is not None else ""
        summaries: list[tuple[Path, FileSummary]] = []
        ordered = sorted(paths, key=lambda p: p.as_posix())
        production = list(sources)
        levels = _levels_by_file([*ordered, *production], config)
        for path in ordered:
            result = _file_result(path, config, cache, shared)
            findings.extend(_file_findings(path, result, levels[path]))
            files[path] = result.waivers
            summaries.append((path, result.summary))
        if cache is not None:
            cache.save()
        findings.extend(_compare_files(summaries, levels, config))
        for path in production:
            source_findings, waivers = _analyze_source(path, config, levels[path])
            findings.extend(source_findings)
            files.setdefault(path, waivers)
        findings.sort(key=lambda f: (f.file.as_posix(), f.line, f.code))
        kept, waived = apply(findings, files)
    return Inspection(findings=kept, waived=waived)


@contextmanager
def _cycle_collector_paused() -> Iterator[None]:
    """Pause Python's cycle collector for the block, if it was running."""
    running = gc.isenabled()
    gc.disable()
    try:
        yield
    finally:
        if running:
            gc.enable()
