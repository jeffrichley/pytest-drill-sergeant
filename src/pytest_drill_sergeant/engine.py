"""The engine: test files and a config in, findings out, with no pytest in sight."""

import ast
import dataclasses
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from pytest_drill_sergeant.cache import Cache, content_hash, context
from pytest_drill_sergeant.checks import CHECKS, Check, Hit, TestFile, TestFunction
from pytest_drill_sergeant.checks.ast_tools import (
    FIXTURE_DECORATORS,
    imports_seen_by,
    module_imports,
    qualified,
)
from pytest_drill_sergeant.checks.base import FileSummary, FunctionNode, Thresholds
from pytest_drill_sergeant.checks.summary import summarize
from pytest_drill_sergeant.config import Config
from pytest_drill_sergeant.findings import Finding, Level
from pytest_drill_sergeant.waivers import (
    FileWaivers,
    WaivedFinding,
    apply,
    parse,
)

__all__ = ["Config", "Inspection", "analyze", "inspect"]


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
    body: list[ast.stmt], names: Mapping[str, str], prefix: str = ""
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
                name=f"{prefix}{node.name}",
                node=node,
                imports=imports_seen_by(node, names),
            )
        elif isinstance(node, ast.ClassDef) and _is_collected_class(node):
            yield from _tests_in(node.body, names, f"{prefix}{node.name}::")


def _ignored_codes(path: Path, config: Config) -> frozenset[str]:
    """The code prefixes the config's per-file ignores turn off for a file.

    A glob matches the file's path relative to the config root, or, for a glob with
    no `/`, the file's name.
    """
    resolved = path.resolve()
    root = config.root.resolve()
    relative = (
        resolved.relative_to(root).as_posix()
        if resolved.is_relative_to(root)
        else path.as_posix()
    )
    ignored: set[str] = set()
    for glob, codes in config.per_file_ignores:
        if fnmatch(relative, glob) or ("/" not in glob and fnmatch(path.name, glob)):
            ignored |= codes
    return frozenset(ignored)


@dataclass(frozen=True)
class Inspection:
    """What one run over the test files found.

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
        hits: Each check's hits in the file, by the check's code.
        summary: The file's per-file summary.
        waivers: The file's inline waivers, for applying after cross-file analysis.
    """

    hits: Mapping[str, tuple[Hit, ...]]
    summary: FileSummary
    waivers: FileWaivers


# The config fields per-file analysis never reads: changing one of them keeps every
# cached result. Every other field is part of the cache key, so a field added to
# the config invalidates the cache until it is listed here.
_NOT_PER_FILE = frozenset(
    {"mode", "levels", "per_file_ignores", "root", "voice", "max_findings", "cache"}
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
    waivers = parse(source) if config.inline_waivers else ()
    file = TestFile(
        path=path,
        module=module,
        tests=tests,
        waivers=waivers,
        thresholds=_thresholds(config),
    )
    return _FileResult(
        hits={check.code: tuple(check.find(file)) for check in CHECKS},
        summary=summarize(file),
        waivers=FileWaivers(
            waivers=waivers, def_lines={t.name: t.node.lineno for t in tests}
        ),
    )


def _file_result(
    path: Path, config: Config, cache: Cache | None, shared: str
) -> _FileResult:
    """A file's per-file result: from the cache when its key still matches."""
    source = path.read_bytes()
    if cache is None:
        return _analyze_file(path, source, config)
    key = f"{content_hash(source)}:{shared}"
    result = cache.get(path, key, _FileResult)
    if result is None:
        result = _analyze_file(path, source, config)
        cache.put(path, key, result)
    return result


def _file_findings(path: Path, result: _FileResult, config: Config) -> list[Finding]:
    """A file's findings: its hits, at the level each check reports at there."""
    ignored = _ignored_codes(path, config)
    return [
        _finding(check, path, hit, level)
        for check in CHECKS
        if (level := _level(check, ignored, config)) is not Level.OFF
        for hit in result.hits.get(check.code, ())
    ]


def _compare_files(
    summaries: list[tuple[Path, FileSummary]], config: Config
) -> list[Finding]:
    """Cross-file analysis: the findings comparing every file's summary turns up.

    A file a per-file ignore keeps a check off is left out of that check's
    comparison.
    """
    findings: list[Finding] = []
    ignored = {path: _ignored_codes(path, config) for path, _ in summaries}
    for check in CHECKS:
        levels = {path: _level(check, ignored[path], config) for path in ignored}
        seen = [(p, s) for p, s in summaries if levels[p] is not Level.OFF]
        findings.extend(
            _finding(check, path, hit, levels[path])
            for path, hit in check.find_across(seen, _thresholds(config))
        )
    return findings


def analyze(
    paths: Iterable[Path], config: Config, cache_dir: Path | None = None
) -> list[Finding]:
    """Run every check over the test files and return the findings that stand.

    The same as `inspect(paths, config, cache_dir).findings`.
    """
    return inspect(paths, config, cache_dir).findings


def inspect(
    paths: Iterable[Path], config: Config, cache_dir: Path | None = None
) -> Inspection:
    """Run every check over the test files, then apply their inline waivers.

    Each file is analysed on its own, for its findings and its per-file summary;
    then the summaries, never the files, are compared across files.

    Args:
        paths: The test files to analyse.
        config: The resolved configuration.
        cache_dir: The directory the cache is kept in, or `None` to run uncached.
            With `config.cache` off the run is uncached too. A file whose bytes,
            drill-sergeant and per-file settings are unchanged since a cached run
            isn't analysed again; cross-file analysis always reruns, from the
            summaries.

    Returns:
        The findings that stand and the waived ones, each ordered by file, line
        and code. Checks configured `off` report none, nor do checks a per-file
        ignore names for a file, and none run in `off` mode; in `warn` mode every
        finding is reported as `warn`. With inline waivers off, no finding is
        waived and malformed waivers (DS001) aren't reported.
    """
    findings: list[Finding] = []
    files: dict[Path, FileWaivers] = {}
    if config.mode is Level.OFF:
        return Inspection(findings=findings, waived=[])
    cache = Cache(cache_dir) if cache_dir is not None and config.cache else None
    shared = context(_per_file_settings(config)) if cache is not None else ""
    summaries: list[tuple[Path, FileSummary]] = []
    for path in sorted(paths, key=lambda p: p.as_posix()):
        result = _file_result(path, config, cache, shared)
        findings.extend(_file_findings(path, result, config))
        files[path] = result.waivers
        summaries.append((path, result.summary))
    if cache is not None:
        cache.save()
    findings.extend(_compare_files(summaries, config))
    findings.sort(key=lambda f: (f.file.as_posix(), f.line, f.code))
    kept, waived = apply(findings, files)
    return Inspection(findings=kept, waived=waived)
