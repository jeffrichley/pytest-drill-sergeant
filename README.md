# pytest-drill-sergeant

A pytest plugin and CLI that catch the ways AI coding agents write bad tests:
copy-pasted setup, assertions that prove nothing, mocks asserted on instead of
behaviour, skips added to go green, sleeps, and test files too long to follow. It
reports them as findings in the drill-sergeant voice, and fails the run on the ones
that let a bug through.

**Status:** v1 is being rebuilt from scratch. So far the malformed-waiver check (DS001),
the structure checks (DS101-DS108), the assertion checks (DS201-DS203), the mocking
checks (DS301-DS303), the cheating checks (DS401-DS403), copy-pasted setup (DS501),
near-duplicate tests (DS502), the brittleness checks (DS601-DS603), the exception
checks (DS701, DS702), the flakiness checks (DS801-DS803) and the missing category
marker (DS901) are reported both by the pytest plugin and by
`drill-sergeant check <paths>`; most are off by default until they are proven (see
[Which checks are on](#which-checks-are-on)). The plan is
the [v1 spec](https://github.com/jeffrichley/pytest-drill-sergeant/issues/118). Version
0.4 is archived under the tag `archive/2026-11-19/v0.4/main`.

## Install

Add it as a dev dependency. While v1 is in pre-release, pin the exact version:

```sh
uv add --dev "pytest-drill-sergeant==1.0.0a1"
```

An exact pre-release pin needs no flag. Leave out `--prerelease=allow`: uv writes it
into `uv.lock` as a lock-wide `prerelease-mode`, and `uv sync --locked` then refuses
the lock. A bare `uv add pytest-drill-sergeant` picks the archived 0.4.

## The pytest plugin

Installing the package turns the plugin on: every `pytest` run is a drill-sergeant run.

- After collection it analyses the files that contributed collected tests (doctests
  don't count), once. A narrow run (one file, `-k`, `--lf`) checks only those files.
  The same goes for files whose tests are all deselected (`-m "not slow"`), so the
  plugin can count fewer findings than `drill-sergeant check` over the same paths.
- The tests always run. A findings section headed `drill sergeant` comes after the
  test results; no test items are added.
- When the tests ran and passed but a finding is at the `fail` level, the run exits 1.
  Failing tests keep pytest's own exit code, as does `--collect-only`; warn mode
  leaves the exit code alone.
- The section shows the first `drill_sergeant_max_findings` findings (25 by default,
  0 for all), then `…and N more, run drill-sergeant check for all`. The exit code
  counts every finding.
- The section closes with a tally of the findings by level and the number of waived
  findings.
- Under pytest-xdist the controller analyses; the workers only run tests.
- It registers the configured category markers with pytest, so `--strict-markers`
  accepts them.
- `-p no:drill_sergeant` or `drill_sergeant_mode = "off"` turns it off. Bad config
  is a pytest usage error (exit 4).

## Which checks are on

A check's default level is the lower of two answers
([ADR 0001](docs/adr/0001-check-kinds-cap-the-default-level.md)):

- **Its kind sets the highest level it can have.** A **defect** (the test can't catch
  a bug, cheats, or fails at random) can be at `fail`. A **smell** (the test works but
  costs later: hard to read, breaks on harmless refactors, duplicated) is at most
  `warn`. A **convention** (a house rule some projects follow) is off unless the
  project opts in.
- **Its precision decides whether it is on.** It is on only once it is **proven**:
  a fresh hand-judged sample of real suites with zero false positives allows `fail`;
  under 15%, with each remaining one waived, allows `warn`; 15% or more keeps it off.
  A check that cries wolf teaches people to ignore every finding, so the rest are off
  by default and come on one by one, each in the change that proves it
  ([#171](https://github.com/jeffrichley/pytest-drill-sergeant/issues/171) tracks
  them).

On by default, at `fail`: DS001 malformed-waiver, DS102 no-action-under-test, DS301
mock-only-assertion, DS401 skip-without-reason, DS402 unconditional-skip, DS603 source-text-grep, DS801
sleep-in-test, DS802 wall-clock-read and DS803 unseeded-random. At `warn`: DS101
no-real-assertion, DS103 assert-before-act, DS104 interleaved-act-assert, DS105
long-test, DS106 long-file, DS107 conditional-logic and DS502 near-duplicate-tests.
Every other check is off: DS201-DS203, DS302, DS303, DS403,
DS501, DS601, DS602, DS701 and DS702 until each is proven, and the two conventions:
DS108 (AAA comments) and DS901 (category markers).

Turn an off check on with `drill_sergeant_levels`, at `fail` or `warn`:

```toml
[tool.pytest.ini_options]
drill_sergeant_levels = ["DS101=fail", "DS302=warn"]
```

A family prefix turns on DS108 too: `DS1=fail` asks for AAA comments in every test
unless `DS108=off` follows it. `drill-sergeant explain` lists every check with its
default level and kind.

## Learning a check

Each finding's fix ends by pointing at `drill-sergeant explain DS###`, which works
offline:

- `drill-sergeant explain DS101` prints why the check matters, what it flags and how
  to fix it, then a test it flags and the same test fixed.
- `drill-sergeant explain` lists every check with its default level and kind, as in
  `DS106 long-file [warn, smell]`, and why it matters.
- An unknown code is a usage error (exit 2).

## The agent guide

The agent guide teaches a coding agent the checks before it writes tests, so it
avoids the failure modes instead of learning them from findings. It is generated
from the checks themselves, so it can't drift from them.

- `drill-sergeant agent-guide` prints it: every check with why it matters, a test it
  flags and the fixed test, and the waiver rule.
- `drill-sergeant agent-guide --install`, run at the repo root, writes the guide as
  an Agent Skill and adds a short block to `AGENTS.md`, or to `CLAUDE.md` when only
  that exists (creating `AGENTS.md` when neither does). The skill goes in
  `.agents/skills/drill-sergeant/` beside `AGENTS.md`, or `.claude/skills/drill-sergeant/`
  beside `CLAUDE.md`.
- The block says the repo uses drill-sergeant, points at the skill and `explain`,
  and states the waiver rule: the agent may ask, but adds a waiver or changes config
  only after an explicit yes from a human for that specific finding.
- The block is marked with the drill-sergeant version. Rerun `--install` after
  upgrading: it replaces only that block and leaves the rest of the file alone.

## The cache

Each file's analysis is cached, so a run with nothing changed adds only tens of
milliseconds, and an edit costs only the files it touched.

- The cache lives under pytest's cache directory (`.pytest_cache/d/drill-sergeant/`,
  or under your `cache_dir`), and the plugin and `drill-sergeant check` share it. It
  is the only file a run writes.
- A file is analysed again when its bytes change, when drill-sergeant changes, or
  when an option that shapes per-file analysis does (thresholds, category markers,
  source dirs, inline waivers), or when a test helper module it follows changes (a
  test's real assertion may be in a helper it imports). Changing levels, mode or
  per-file ignores reuses it.
- A corrupt or unreadable cache is rebuilt without a word.
- `drill_sergeant_cache = false` turns it off; so does `-p no:cacheprovider`, which
  turns off pytest's own cache. `pytest --cache-clear` empties it.

## Waivers

When a human agrees that a finding is a false positive, a waiver silences it:

```python
def test_cli_smoke():  # drill: waive DS101 -- the exit code is checked by CI
    main(["--help"])
```

- A waiver is a `# drill: waive DS### -- <reason>` comment on the test's `def` line
  (or the `):` line a wrapped signature closes on),
  where it covers that check anywhere in the test, or on the line the finding is
  reported on. It silences only the check it names.
- The code and the reason are both required. A waiver missing either waives nothing
  and is itself a finding (DS001, `fail`), which no waiver can silence.
- Every run's closing tally counts the waived findings; `drill-sergeant check
  --show-waived` lists each one with its reason. A waiver that matches no finding is
  not reported.
- `drill_sergeant_inline_waivers = false` turns waivers off: their findings stand,
  and DS001 reports nothing. Silencing then goes only through config (levels and
  per-file ignores).

## Configuration

drill-sergeant is configured only through `drill_sergeant_*` options in your pytest
config: no environment variables, no command-line flags. `drill-sergeant check` finds
the config file the way pytest does, searching upward from the paths it checks for
`pytest.toml`, `pytest.ini`, `pyproject.toml` (`[tool.pytest.ini_options]` or
`[tool.pytest]`), `tox.ini` (`[pytest]`) or `setup.cfg` (`[tool:pytest]`);
`--config <file>` names one instead, read as pytest's `-c` reads it (a `.toml` not
named `pytest.toml` is read like a `pyproject.toml`), and refused when it holds no
pytest table. Because of that search, `check` on a sub-package with its own pytest
config (say `pkg/pyproject.toml`) uses that package's config, not the root's; pass
`--config` to choose. An unknown `drill_sergeant_*` option, unknown
check code, bad level or non-numeric threshold is a usage error (exit 2 from the CLI, 4 from pytest).

```toml
[tool.pytest.ini_options]
drill_sergeant_mode = "warn"
drill_sergeant_levels = ["DS1=warn", "DS101=fail"]
drill_sergeant_per_file_ignores = ["tests/legacy/*: DS101"]
drill_sergeant_voice = false
```

| Option | Value | Default |
|---|---|---|
| `drill_sergeant_mode` | `fail`, `warn` (findings show, the exit code is unchanged) or `off` (no check runs) | `fail` |
| `drill_sergeant_levels` | `CODE=level` lines; a family prefix (`DS1`, `DS1xx`) covers the family; the most specific entry wins | each check's default |
| `drill_sergeant_per_file_ignores` | `glob: codes` lines, globs relative to the config file; a glob with no `/` also matches file names | none |
| `drill_sergeant_max_file_lines` | whole number | 500 |
| `drill_sergeant_max_test_lines` | whole number: the most lines of code a test may have; `drill-sergeant explain DS105` says what counts | 50 |
| `drill_sergeant_max_mock_setup` | whole number | 10 |
| `drill_sergeant_max_act_assert_cycles` | whole number: the most act-then-assert cycles a test may have before DS104 flags it; 1, the least it counts as, flags a test at its second | 2 |
| `drill_sergeant_duplicate_setup_min_statements` | whole number | 3 |
| `drill_sergeant_duplicate_setup_min_tests` | whole number | 3 |
| `drill_sergeant_category_markers` | marker names; with DS901 on, every test must carry one; the plugin registers them | `unit integration e2e` |
| `drill_sergeant_source_dirs` | directory lines, relative to the config file; each must exist. The production code DS403 reads in full; with none and no `src/`, DS403, when on, is skipped and the output says so | `src/` if it exists |
| `drill_sergeant_voice` | `true` or `false`; off prints Found/Why/Fix without the voice | `true` |
| `drill_sergeant_max_findings` | whole number, 0 for all | 25 |
| `drill_sergeant_inline_waivers` | `true` or `false` | `true` |
| `drill_sergeant_cache` | `true` or `false`; off analyses every file on every run | `true` |

### Category markers

DS901, off by default, requires every test to carry one of the configured category
markers, as `pytest.mark.<marker>` on the test, its class or the module's
`pytestmark`. Its fix
suggests the marker named by the nearest directory in the file's path, relative to the
config file's directory (`tests/integration/test_x.py` suggests
`@pytest.mark.integration`), and otherwise lists the configured markers. The check
reads the files, never edits them.

**Known limitation:** markers a project's own conftest hook adds at collection time
(`pytest_collection_modifyitems` marking by directory, say) are not in the test files,
so the check can't see them. Such projects leave it off. Others turn it on with
`drill_sergeant_levels = ["DS901=fail"]`.

## Development

```sh
just sync           # create .venv with the dev tools
just install-hooks  # pre-commit and commit-msg hooks
just check          # the gate: lint, format, types, dead code, tests
just perf           # the speed budget: a warm run over 300 test files (not in the gate)
just try ../other/tests DS101 DS103  # this checkout on another project's tests
```

`just try <path>` runs this checkout's `drill-sergeant check <path>` with that project's
own config. Codes after the path also turn those checks on at `fail`, for that run
only: it writes a temporary config file beside the project's, with the codes appended
to `drill_sergeant_levels`, passes it with `--config` and deletes it afterwards. The
project's files are left as they were; only a run killed outright leaves a
`.drill-sergeant-try-*.toml` behind.

## License

MIT
