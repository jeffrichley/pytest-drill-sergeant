# pytest-drill-sergeant

A pytest plugin and CLI that catch the ways AI coding agents write bad tests:
copy-pasted setup, assertions that prove nothing, mocks asserted on instead of
behaviour, skips added to go green, sleeps, and test files too long to follow. It
reports them as findings that fail the run, in the drill-sergeant voice.

**Status:** v1 is being rebuilt from scratch. So far `drill-sergeant check <paths>`
reports tests with no real assertion (DS101) and exits 1 when it finds any; the pytest
plugin does nothing yet. The plan is the
[v1 spec](https://github.com/jeffrichley/pytest-drill-sergeant/issues/118). Version
0.4 is archived under the tag `archive/2026-11-19/v0.4/main`.

## Configuration

drill-sergeant is configured only through `drill_sergeant_*` options in your pytest
config: no environment variables, no command-line flags. `drill-sergeant check` finds
the config file the way pytest does, searching upward from the paths it checks for
`pytest.toml`, `pytest.ini`, `pyproject.toml` (`[tool.pytest.ini_options]` or
`[tool.pytest]`), `tox.ini` (`[pytest]`) or `setup.cfg` (`[tool:pytest]`);
`--config <file>` names one instead. An unknown `drill_sergeant_*` option, unknown
check code, bad level or non-numeric threshold is a usage error (exit 2).

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
| `drill_sergeant_max_test_lines` | whole number | 50 |
| `drill_sergeant_max_mock_setup` | whole number | 10 |
| `drill_sergeant_duplicate_setup_min_statements` | whole number | 3 |
| `drill_sergeant_duplicate_setup_min_tests` | whole number | 3 |
| `drill_sergeant_category_markers` | marker names | `unit integration e2e` |
| `drill_sergeant_source_dirs` | directory lines | `src/` if it exists |
| `drill_sergeant_voice` | `true` or `false`; off prints Found/Why/Fix without the voice | `true` |
| `drill_sergeant_max_findings` | whole number, 0 for all | 25 |
| `drill_sergeant_inline_waivers` | `true` or `false` | `true` |
| `drill_sergeant_cache` | `true` or `false` | `true` |

The thresholds, markers, source dirs, finding cap, waivers and cache are accepted now
and take effect as the checks and plugin that use them land.

## Development

```sh
just sync           # create .venv with the dev tools
just install-hooks  # pre-commit and commit-msg hooks
just check          # the gate: lint, format, types, dead code, tests
```

## License

MIT
