# Pytest Drill Sergeant Recovery Plan

Purpose: get this project back to predictable, low-drama operation with clear gates for plugin behavior, config loading, and CI quality.

## Guiding Principles

- Stabilize before expanding scope.
- One source of truth per concern (plugin hooks, config, quality gate entrypoints).
- Prefer deterministic failures over hidden warnings.
- Ship in small phases with hard acceptance criteria.

---

## Phase 0 - Reset Baseline (No New Features)

### Objectives

- Establish a reproducible baseline on `main`.
- Capture current behavior and known instability points.

### Steps

- [x] Create a `baseline` report from local run:
  - [x] `uv run pytest -q`
  - [x] `uv run ruff check src tests`
  - [x] `uv run mypy src tests --config-file=pyproject.toml`
- [x] Save output snapshots under `planning/baseline/`.
- [x] Record current known warnings/errors and expected exit codes.
- [x] Add a short `CURRENT_STATE.md` with “what works / what is noisy”.

### Exit Criteria

- [x] Everyone agrees on baseline outputs and pain points.

---

## Phase 1 - Plugin Lifecycle Hardening

### Objectives

- Make plugin option registration and hook execution reliable.
- Remove hidden failure paths and stdout noise from runtime hooks.

### Steps

- [x] Unify pytest plugin entrypoint behavior:
  - [x] Ensure `pytest_addoption` is always registered from the loaded plugin module.
  - [x] Verify no `PytestConfigWarning` for `drill_sergeant_*` options.
- [x] Replace `print(...)` calls in plugin/validators with controlled pytest logging/reporting.
- [x] Replace broad hook swallowing with explicit, actionable failures (or debug-only diagnostics).
- [x] Add tests that assert plugin load + option registration in isolated `pytester` runs.
- [x] Add tests for disabled mode (`drill_sergeant_enabled = false`) to verify zero enforcement.

### Exit Criteria

- [x] `uv run pytest -q` passes with no drill-sergeant config warnings.
- [x] Plugin hooks do not emit uncontrolled console output.

---

## Phase 2 - Config System Consolidation

### Objectives

- Clarify and enforce config precedence.
- Support project TOML config intentionally (or explicitly defer it).

### Target Precedence (proposed)

1. Environment variables
2. Pytest config (`pytest.ini` / pytest TOML config)
3. `[tool.drill_sergeant]` in `pyproject.toml`
4. Code defaults

### Steps

- [x] Decide final config precedence and document it in README.
- [x] Implement TOML parsing for `[tool.drill_sergeant]` and marker mappings.
- [x] Remove duplicate/fallback parsing paths that cause ambiguity.
- [x] Add table-driven tests for each option across all config layers.
- [x] Add a `--drill-sergeant-debug-config` mode (or env flag) to print effective config once.

### Exit Criteria

- [x] Config values are deterministic and covered by tests.
- [x] README config examples match real behavior.

---

## Phase 3 - Rule Semantics Cleanup (AAA / Marker / File Length / Return Type)

### Objectives

- Make each rule’s intent sharp and non-overlapping.
- Reduce “surprise failures” during normal developer workflow.

### Steps

- [x] Marker rule:
  - [x] Confirm marker discovery from pytest marker config works in ini and TOML contexts.
  - [x] Confirm auto-detection behavior for nested test paths and custom mappings.
- [x] AAA rule:
  - [x] Define accepted comment grammar explicitly.
  - [x] Validate synonym behavior with clear examples/tests.
- [x] File-length rule:
  - [x] Decide whether this is hard fail vs warning-only mode.
  - [x] Add per-path ignore capability if needed.
- [x] Return-type rule:
  - [x] Decide if runtime enforcement stays, or defer to static tooling.
  - [x] Remove plugin runtime return-type enforcement and options.
  - [x] Enable Ruff `ANN` as the canonical return-annotation enforcement path.
  - [x] Document migration in README.

### Exit Criteria

- [x] Each rule has explicit behavior contract and tests.
- [x] No duplicated responsibility without rationale.

---

## Phase 4 - CI and Developer Workflow Simplification

### Objectives

- One reliable command path locally and in CI.
- Reduce “works locally, fails in CI” drift.

### Steps

- [x] Define canonical commands:
  - [x] `uv run pytest -q`
  - [x] `uv run ruff check src tests`
  - [x] `uv run mypy src tests --config-file=pyproject.toml`
- [x] Align `just` and GitHub workflows to these same commands.
- [x] Remove or quarantine novelty/non-critical CI jobs from required checks.
- [x] Add a single `just verify` target that mirrors required CI gates.
- [x] Ensure Python version matrix only where it adds real signal.

### Exit Criteria

- [x] Same commands pass locally and in required CI.
- [x] Required checks are understandable in <60 seconds.

---

## Phase 5 - Quality of Life and Documentation Refresh

### Objectives

- Make onboarding friction low.
- Make failures self-explanatory.

### Steps

- [x] Rewrite README sections to match current architecture (no roadmap leakage).
- [x] Add “quick start” with a minimal valid `pytest.ini` and expected outcomes.
- [x] Add `docs/Failure-Catalog.md` mapping each rule violation to fix examples.
- [x] Add `docs/Decision-Log.md` for rule scope decisions (especially return type).
- [x] Add release checklist for future tags.

### Exit Criteria

- [x] New contributor can run checks and understand failures without tribal knowledge.

---

## Phase 6 - Optional Modernization (Only After Stability)

### Objectives

- Improve internals without destabilizing public behavior.

### Steps

- [ ] Evaluate converting validators to a registry pattern with explicit lifecycle.
- [ ] Evaluate introducing severity levels (error/warn/info) per rule.
- [ ] Evaluate plugin telemetry hooks for large test suites.
- [ ] Consider extracting config parsing into dedicated module with schema validation.

### Exit Criteria

- [ ] Modernization tasks are sequenced and non-blocking.

---

## Operational Cadence

- [ ] Weekly 30-minute checkpoint: close completed checkboxes, trim stale tasks.
- [ ] Open PRs scoped to one phase or sub-phase only.
- [ ] Every merged PR must include:
  - [ ] tests proving behavior,
  - [ ] docs updates if behavior changed,
  - [ ] no new warning classes in baseline run.

---

## Definition of "Good Again"

Project is considered recovered when all are true:

- [x] Plugin loads cleanly with zero unknown config warnings.
- [x] Config precedence is deterministic and documented.
- [x] Core rules behave as documented with strong test coverage.
- [x] Local and CI verification commands are identical and reliable.
- [x] Team can explain enforcement behavior without reading source code.

---

## Current Status

As of 2026-02-13, recovery criteria are met and the project is considered **stabilized**.

- Phases 0 through 5 are complete.
- Required CI gates are stable and deterministic.
- Documentation, failure guidance, and release checklist are now in-repo.
- Remaining work is optional modernization in Phase 6.

---

## Progress Note (2026-02-13)

- Return-type enforcement is no longer implemented in plugin runtime validators.
- Ruff annotations rules (`ANN`) are enabled in `pyproject.toml`.
- `ruff check --fix` is now the supported auto-fix path for return annotations.
- Validation snapshot after migration:
  - `uv run pytest -q` -> pass
  - `uv run ruff check src tests` -> pass
  - `uv run mypy src tests --config-file=pyproject.toml` -> pass
- CI workflow has been simplified to explicit `test` / `lint` / `typecheck` gates (plus informational coverage).
- Dependabot backlog was triaged and resolved (merged or closed if superseded).
- Phase 5 documentation deliverables landed:
  - `README.md` (architecture-aligned with Drill Sergeant voice)
  - `docs/Failure-Catalog.md`
  - `docs/Decision-Log.md`
  - `docs/Release-Checklist.md`
