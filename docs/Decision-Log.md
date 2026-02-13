# Decision Log

Purpose: capture project-level decisions that affect behavior, scope, and maintenance.

## 2026-02-13: Remove Runtime Return-Type Enforcement

### Decision

- Removed plugin runtime return-type rule and auto-fix behavior.
- Standardized on Ruff annotations (`ANN`) for return-type enforcement.

### Why

- Return annotations are better enforced by static tools than runtime test hooks.
- Avoid duplicated responsibility between plugin and lint/typecheck stack.
- Reduces plugin complexity and surprise side effects.

### Impact

- Removed return-type validator and related config options.
- Added Ruff `ANN` selection in lint policy.
- `ruff check --fix` is the preferred auto-fix path.

## 2026-02-13: CI Contract Simplification

### Decision

- Required checks reduced to explicit gates:
  - tests
  - ruff lint
  - mypy typecheck
- Coverage remains informational.

### Why

- Faster CI feedback and lower operational noise.
- Better local/CI parity with `just verify`.

### Impact

- Removed Nox-driven CI orchestration.
- Removed low-signal stats workflow from required path.
- Established deterministic quality gate contract in README.

## 2026-02-13: Config Precedence Contract

### Decision

Final precedence is:

1. Environment variables
2. Pytest config (`pytest.ini` / `[tool.pytest.ini_options]`)
3. `[tool.drill_sergeant]` in `pyproject.toml`
4. Defaults

### Why

- Makes behavior predictable and easy to reason about.
- Supports project defaults with targeted overrides.

### Impact

- Config loading consolidated and covered by tests.
- README and tests aligned to this precedence model.

## 2026-02-13: Phase 6 Internal Modernization

### Decision

- Introduced a validator registry (`validators/registry.py`) used by plugin orchestration.
- Added marker/AAA severity controls (`error`, `warn`, `off`) while preserving default fail behavior.
- Added optional validator timing telemetry via `DRILL_SERGEANT_DEBUG_TELEMETRY=true`.
- Split config validation/normalization into `config_schema.py`.

### Why

- Simplifies validator lifecycle wiring and future rule extension.
- Supports gradual rollout with warning mode where needed.
- Improves debuggability for large suites.
- Makes config behavior explicit and fail-fast for invalid values.

### Impact

- New config fields:
  - `marker_severity`
  - `aaa_severity`
- New env vars:
  - `DRILL_SERGEANT_MARKER_SEVERITY`
  - `DRILL_SERGEANT_AAA_SEVERITY`
  - `DRILL_SERGEANT_DEBUG_TELEMETRY`
- Invalid mode values now raise explicit configuration errors.

## 2026-02-13: Adopt release-please for Versioning and Release PRs

### Decision

- Added `release-please` automation for release PR and tag/release creation.
- Production publish now triggers from GitHub release publish event.

### Why

- Removes manual version/tag churn.
- Standardizes changelog generation from commit history.
- Makes release process auditable and repeatable.

### Impact

- New workflow: `.github/workflows/release-please.yml`
- New config:
  - `.github/release-please-config.json`
  - `.github/.release-please-manifest.json`
- Updated publish trigger in `.github/workflows/release.yml` to `release: published`.
