# Pytest Drill Sergeant

[![CI Status](https://github.com/jeffrichley/pytest-drill-sergeant/workflows/CI/badge.svg)](https://github.com/jeffrichley/pytest-drill-sergeant/actions)
[![codecov](https://codecov.io/gh/jeffrichley/pytest-drill-sergeant/branch/main/graph/badge.svg)](https://codecov.io/gh/jeffrichley/pytest-drill-sergeant)
[![PyPI version](https://badge.fury.io/py/pytest-drill-sergeant.svg)](https://badge.fury.io/py/pytest-drill-sergeant)

You want elite tests?
Then stop writing lazy chaos and start writing disciplined test code.

This plugin is your no-excuses drill instructor for:

- marker classification
- AAA structure (`Arrange` / `Act` / `Assert`)
- file-length discipline

It does not care about feelings. It cares about standards.

## Mission Profile

### 1. Marker Rule

What it does:

- validates useful test markers
- auto-detects marker intent from path (for example `tests/unit/` -> `@pytest.mark.unit`)
- supports custom directory-to-marker mappings
- reads marker declarations from both `pytest.ini` and `pyproject.toml` (`[tool.pytest.ini_options]`)

What you do:

- put tests in intentional directories
- keep marker declarations real
- stop shipping unclassified tests

### 2. AAA Rule

What it does:

- enforces explicit AAA section comments in test bodies
- supports two modes:
  - `basic`: section presence required
  - `strict`: presence + order + no duplicate section declarations
- supports built-in/custom synonyms when enabled

Accepted grammar:

```text
# <Keyword> - <description>
```

Examples:

```python
# Arrange - create test fixture
# Act - call the function
# Assert - verify expected behavior
```

### 3. File-Length Rule

What it does:

- enforces max test file length
- supports modes:
  - `error`: fail
  - `warn`: report only
  - `off`: disabled
- supports path exclusions and inline ignore token

Inline ignore example:

```python
# drill-sergeant: file-length ignore
```

Use this sparingly. If you need it everywhere, the file should be split.

## Quick Start

### Install

```bash
uv add --group dev pytest-drill-sergeant
```

### Minimal `pytest.ini`

```ini
[pytest]
addopts = -p drill_sergeant
markers =
    unit: Unit tests
    integration: Integration tests

drill_sergeant_enabled = true
drill_sergeant_enforce_markers = true
drill_sergeant_enforce_aaa = true
drill_sergeant_enforce_file_length = true
drill_sergeant_marker_severity = error
drill_sergeant_aaa_severity = error
drill_sergeant_aaa_mode = basic
drill_sergeant_auto_detect_markers = true
drill_sergeant_max_file_length = 350
```

### Minimal Passing Test

```python
import pytest


@pytest.mark.unit
def test_addition() -> None:
    # Arrange - prepare operands
    left = 2
    right = 3

    # Act - run operation
    total = left + right

    # Assert - validate result
    assert total == 5
```

## Configuration

Precedence (highest to lowest):

1. environment variables
2. pytest config (`pytest.ini` or `[tool.pytest.ini_options]`)
3. `[tool.drill_sergeant]` in `pyproject.toml`
4. plugin defaults

### `pyproject.toml` Example

```toml
[tool.drill_sergeant]
enabled = true
enforce_markers = true
enforce_aaa = true
aaa_mode = "basic"
marker_severity = "error"
aaa_severity = "error"
enforce_file_length = true
file_length_mode = "error"
file_length_exclude = ["tests/legacy/*"]
file_length_inline_ignore = true
file_length_inline_ignore_token = "drill-sergeant: file-length ignore"
auto_detect_markers = true
min_description_length = 3
max_file_length = 350
aaa_synonyms_enabled = false
aaa_builtin_synonyms = true

[tool.drill_sergeant.marker_mappings]
contract = "api"
smoke = "integration"
```

### Environment Variables

- `DRILL_SERGEANT_ENABLED`
- `DRILL_SERGEANT_ENFORCE_MARKERS`
- `DRILL_SERGEANT_ENFORCE_AAA`
- `DRILL_SERGEANT_MARKER_SEVERITY` (`error` | `warn` | `off`)
- `DRILL_SERGEANT_AAA_SEVERITY` (`error` | `warn` | `off`)
- `DRILL_SERGEANT_AAA_MODE`
- `DRILL_SERGEANT_ENFORCE_FILE_LENGTH`
- `DRILL_SERGEANT_FILE_LENGTH_MODE`
- `DRILL_SERGEANT_FILE_LENGTH_EXCLUDE`
- `DRILL_SERGEANT_FILE_LENGTH_INLINE_IGNORE`
- `DRILL_SERGEANT_FILE_LENGTH_INLINE_IGNORE_TOKEN`
- `DRILL_SERGEANT_AUTO_DETECT_MARKERS`
- `DRILL_SERGEANT_MIN_DESCRIPTION_LENGTH`
- `DRILL_SERGEANT_MAX_FILE_LENGTH`
- `DRILL_SERGEANT_MARKER_MAPPINGS`
- `DRILL_SERGEANT_DEBUG_CONFIG`
- `DRILL_SERGEANT_DEBUG_TELEMETRY` (prints per-validator timing summary at session end)

## Return Type Policy

Return-type annotation enforcement is intentionally handled by static tooling, not runtime test hooks.

Use Ruff `ANN` rules:

```bash
uv run ruff check --fix src tests
```

## CI Contract

Required gates:

- `uv run pytest -q`
- `uv run ruff check src tests`
- `uv run mypy src tests --config-file=pyproject.toml`

Local parity command:

```bash
just verify
```

Coverage is informational, not a required merge gate.

## Failure Intel

If a rule fails, use:

- `docs/Failure-Catalog.md` for failure-to-fix mapping
- `docs/Decision-Log.md` for scope decisions and rationale
- `docs/Release-Checklist.md` for release execution
- `STABILIZATION_PLAN.md` for phased recovery status

## Development

Common commands:

```bash
just verify
just test
just lint
just type-check
```

## Final Word

The point is not ceremony.
The point is predictable, readable, maintainable test code under pressure.

Do the basics with discipline and your test suite will stop betraying you.

## License

MIT
