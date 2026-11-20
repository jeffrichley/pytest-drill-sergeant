"""The pytest plugin, registered through the `pytest11` entry point.

Installing the package turns it on; `-p no:drill_sergeant` or
`drill_sergeant_mode = off` turns it off. After collection it analyses the files that
contributed collected test functions, and the production code, once, on the xdist
controller only; the tests then run as always. The findings section after the test results shows them, and a
run whose tests ran and passed exits 1 when any finding is at the `fail` level.

Per-file results are cached under pytest's cache directory, shared with the CLI,
unless `drill_sergeant_cache = false` or `-p no:cacheprovider`; the cache is the
only file the plugin writes.
"""

from collections.abc import Generator
from pathlib import Path

import pytest
from rich.console import Console

from pytest_drill_sergeant.cache import CACHE_NAME
from pytest_drill_sergeant.config import (
    OPTIONS,
    PREFIX,
    Config,
    ConfigError,
    RawValue,
    refusal,
    resolve,
)
from pytest_drill_sergeant.engine import Inspection, inspect
from pytest_drill_sergeant.findings import Level
from pytest_drill_sergeant.paths import relative
from pytest_drill_sergeant.production import production_code
from pytest_drill_sergeant.render import render

# The name the run's state is registered under with pytest's plugin manager.
_RUN = "drill_sergeant_run"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register every `drill_sergeant_*` ini option."""
    for option in OPTIONS:
        parser.addini(
            option.name, option.help, type=option.kind, default=option.default
        )


def _raw_value(config: pytest.Config, name: str) -> RawValue:
    """An option's value as pytest has it, or as written when pytest can't type it.

    pytest refuses an int or bool it can't parse in its own words; handing
    `resolve` the value as written lets it refuse in the same words as the CLI.
    """
    try:
        value: RawValue = config.getini(name)
    except (ValueError, TypeError):
        # `inicfg` is pytest's compatibility view of the ini values as written.
        value = config.inicfg[name]
    return value


def _require_config(config: pytest.Config) -> Config:
    """The resolved drill-sergeant config.

    Raises:
        pytest.UsageError: When the config is wrong, naming what in one line, as
            the CLI does.
    """
    # pytest offers no other public way to list the keys a config file sets, and
    # `getini` can only ask after a key by name, so an unknown `drill_sergeant_*`
    # key is found through `inicfg`, pytest's compatibility view of them.
    raw: dict[str, RawValue] = {
        key: "" for key in config.inicfg if key.startswith(PREFIX)
    }
    raw.update({option.name: _raw_value(config, option.name) for option in OPTIONS})
    root = config.inipath.parent if config.inipath else config.rootpath
    try:
        return resolve(raw, root=root, source=config.inipath)
    except ConfigError as error:
        raise pytest.UsageError(refusal(error)) from None


def pytest_configure(config: pytest.Config) -> None:
    """Resolve the config, register the category markers and start the run.

    The markers are registered whatever the mode, so `--strict-markers` accepts them;
    the run starts unless the mode is `off`.

    An xdist worker only runs tests and tells the controller which files it collected
    them from; the controller analyses.
    """
    resolved = _require_config(config)
    for marker in resolved.category_markers:
        config.addinivalue_line("markers", f"{marker}: a category marker")
    if resolved.mode is Level.OFF:
        return
    if hasattr(config, "workerinput"):
        config.pluginmanager.register(_Worker(config), _RUN)
    else:
        config.pluginmanager.register(_Run(config, resolved), _RUN)


# The key under which an xdist worker sends the controller its collected files.
_FILES = "drill_sergeant_files"


def _collected_files(session: pytest.Session) -> set[Path]:
    """The files that contributed collected tests: test functions, not doctests."""
    return {item.path for item in session.items if isinstance(item, pytest.Function)}


class _Worker:
    """An xdist worker's part: report the files it collected tests from."""

    def __init__(self, config: pytest.Config) -> None:
        self.config = config

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        """Hand the collected files to the controller."""
        output = self.config.workeroutput  # type: ignore[attr-defined]  # set by xdist
        output[_FILES] = sorted(str(path) for path in _collected_files(session))


class _Run:
    """One drill-sergeant run: the files analysed, what they hold, the report."""

    def __init__(self, config: pytest.Config, resolved: Config) -> None:
        self.config = config
        self.resolved = resolved
        self.inspection: Inspection | None = None
        self.production = production_code(resolved, config.invocation_params.dir)

    def _analyze(self, paths: set[Path]) -> None:
        if self.inspection is not None:
            return
        here = self.config.invocation_params.dir
        self.inspection = inspect(
            sorted(relative(p, here) for p in paths),
            self.resolved,
            self.production.files,
            cache_dir=self._cache_dir(),
        )

    def _cache_dir(self) -> Path | None:
        """The cache's directory under pytest's cache directory, if pytest has one.

        Under `-p no:cacheprovider` pytest has none, and the run is uncached.
        """
        cache = getattr(self.config, "cache", None)
        if cache is None or not self.resolved.cache:
            return None
        directory: Path = cache.mkdir(CACHE_NAME)
        return directory

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        """Analyse the files that contributed collected tests."""
        self._analyze(_collected_files(session))

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodedown(self, node: object) -> None:
        """Analyse the files the first xdist worker to finish collected tests from.

        Every worker collects the same tests, so one worker's files are the run's.
        """
        files = getattr(node, "workeroutput", {}).get(_FILES)
        if files is not None:
            self._analyze({Path(file) for file in files})

    # A wrapper called first is the outermost, so its code after `yield` runs after
    # the terminal reporter's own, which ends with the short test summary.
    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_terminal_summary(
        self, terminalreporter: pytest.TerminalReporter
    ) -> Generator[None]:
        """Show the findings section after the test results and their summary."""
        result = yield
        if self.inspection is None:
            return result
        terminalreporter.write_sep("=", "drill sergeant")
        writer = self.config.get_terminal_writer()
        # Width and colour are pytest's own, so the section matches the run's output
        # and follows `--color`.
        console = Console(
            file=writer,  # type: ignore[arg-type]  # it writes text, as Rich needs
            width=writer.fullwidth,
            force_terminal=writer.hasmarkup,
            no_color=not writer.hasmarkup,
            color_system="standard" if writer.hasmarkup else None,
            highlight=False,
        )
        if self.production.note:
            # One line, as it stands, however narrow the terminal.
            console.print(self.production.note, soft_wrap=True, markup=False)
        console.print(
            render(
                self.inspection.findings,
                waived=self.inspection.waived,
                voice=self.resolved.voice,
                max_findings=self.resolved.max_findings,
            ),
            crop=False,
        )
        return result

    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        """Fail a run whose tests ran and passed when a finding is at `fail` level."""
        if (
            session.exitstatus == pytest.ExitCode.OK
            and not self.config.option.collectonly
            and self.inspection is not None
            and any(f.level is Level.FAIL for f in self.inspection.findings)
        ):
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
