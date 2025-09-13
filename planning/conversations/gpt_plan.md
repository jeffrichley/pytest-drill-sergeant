Awesome — I pulled the key ideas from our chats and shaped them into a concrete system design for the plugin. Here’s a crisp, implementation-ready architecture.

pytest-drill-sergeant — Design & Architecture
1) Problem & Goals

AI coders tend to write tests that lock in how code works (internals, call order, private members) instead of what it does (public behavior). We want a pytest plugin that detects “HOW smells,” nudges authors toward behavior-focused tests, and makes it fun with persona-based feedback and a “Battlefield Readiness Score.”

2) High-Level Architecture

Hybrid layout (shared engine + plugin + CLI)

ai_guardrails/core: static analyzers (AST), clone/fixture detectors, scoring, SARIF/JSON reporters.

ai_guardrails/pytest_plugin: pytest hooks, per-test runtime signals (coverage, mock usage), persona output.

ai_guardrails/cli: standalone ai-guardrails lint for repo-wide static checks & CI SARIF export.

Single source of truth config in pyproject.toml so CLI and plugin behave identically.

ai_guardrails/
  src/ai_guardrails/core/
    models.py          # Finding, Rule, Cluster, Severity
    tokenize_ast.py    # AST normalizer, n-grammer, SimHash/MinHash
    aaa.py             # AAA comment detector
    clones.py          # near-duplicate tests
    fixtures.py        # repeated Arrange → fixture/factory suggestions
    report.py          # JSON/MD
    sarif.py           # SARIF writer
  src/ai_guardrails/pytest_plugin/
    plugin.py          # hooks: collect, runtest_logreport, terminal_summary
    coverage.py        # per-test coverage integration
  src/ai_guardrails/cli/
    main.py            # ai-guardrails lint --format sarif|json|md


3) Core Signals & Detectors (WHAT vs HOW)
Static (AST)

Private-surface access: imports/attributes starting with _ from the SUT → strong HOW.

Mock/spy over-spec: assert_called_*, assert_has_calls, etc. (allowlist for true boundaries).

Call-graph expectations: patch targets inside internal modules / not exported in __all__.

Over-specific exception messages (e.g., long exact text) — prefer type or key tokens.

Structural equality on internals: comparing __dict__, vars(), dataclasses.asdict(), or repr(obj) to strings.

AAA comment advisor: detect missing/mis-ordered “Arrange/Act/Assert” tags and surface as advice, not failures.

Dynamic (per-test at runtime)

Coverage-to-Assertion Ratio (CAR): high lines covered with few public assertions ⇒ likely internals poking.

Mock assert usage counts (runtime) to quantify overspec.

Redundancy & Fixture Quality

Static near-duplicate clustering: AST normalization + n-gram/MinHash/SimHash → clusters of isomorphic tests.

Dynamic behavior clustering: per-test coverage signatures + Jaccard ≥ 0.95; also compare assert “shapes.”

Parametrization suggester: if K≈3+ tests differ only in small literal sets, propose @pytest.mark.parametrize with a table.

Fixture extraction: repeated Arrange fingerprints ⇒ propose fixture or factory; name from noun-phrases.

4) Scoring & Reporting
Behavior Integrity Score (BIS)

Rule-based weighted score per test; penalize private access, patched internals, over-specific exception messages, structural equality, excessive mock assertions; reward public-API assertions. Thresholds: ≥85 Good, 70–84 Caution, <70 Drifting into HOW.

Battlefield Readiness Score (BRS)

One repo score with components: AAA%, duplicate penalty, parametrization rate, fixture reuse, non-determinism, slow tests, style smells; surfaced each run and in CI.

Outputs

Terminal summary: BIS distribution, top HOW smells, duplicate clusters, CAR histogram.

Per-test advisory sections: friendly rewrite tips; never block by default.

Artifacts: report.json + SARIF for PR annotations; trendable telemetry blob.

5) Personas & Humor Layer

Use Strategy pattern: each persona exposes methods like on_pass(item), on_fail(item, finding), on_summary(metrics) and returns template strings that the plugin fills (test id, counts, etc.). Hook into pytest_runtest_makereport / pytest_terminal_summary to inject persona lines on pass/fail/summary.

Examples (config-selectable): “Drill Sergeant Hartman” (snarky), “Motivational Coach,” “Sarcastic Butler,” “Pirate,” etc.

6) Pytest Hook Flow

Collection: run AST passes, compute per-test features, attach metadata to Item.

Execution: per-test coverage context, count mock asserts, capture over-specific exception text via pytest_assertrepr_compare.

Summary: compute BIS & BRS; emit per-test advisories, persona quips, JSON/SARIF.

7) Configuration (single source in pyproject.toml)

mode: advisory | quality-gate | strict with “budget.warn/error”.

enable/suppress: fine-grained rule toggles.

Thresholds: static_clone_hamming, dynamic_cov_jaccard, param_candidate_k.

SUT detection: ds_sut_top_pkg or auto-detect; allowlisted mock targets (e.g., requests.*, time.*).

CLI mirrors plugin behavior.

8) CI & Workflow

Local: ai-guardrails lint . (advisory); pytest -q with per-test advisories and personas.

PR: job 1 — static lint → upload SARIF; job 2 — pytest --guardrails-mode=quality-gate to softly enforce budgets.

Nightly: optional strict subset (secrets/timeouts).

9) Data Model (core)

Finding {rule_id, severity, path, location, message, test_nodeid?}
Cluster {kind: "static"|"dynamic", members: [nodeid], similarity}
Rule {id, category, default_severity, description}
RunMetrics {AAA_rate, duplicate_penalty, param_rate, fixture_reuse_rate, non_determinism_rate, slow_tests_rate, style_smell_rate, BIS_stats, CAR_hist, clusters}
(Aligned with the BRS and BIS formulas).

10) Extensibility

Rules as plugins inside ai_guardrails/core (registry pattern); users can toggle or extend.

Classifier upgrade path: swap the weighted BIS for a simple logistic regression trained on labeled tests; keep features stable.

Personas: add new Strategy classes without changing core logic.

11) Performance & DX

AST passes run once at collection; dynamic coverage per test uses coverage.py “test context” mode.

All “advice” by default to avoid noisy failures; strictness opt-in.

12) Phased Delivery (Minimal Path to Green)

Phase 1 — Static Guards: private access, patched internals, exception message overspec, structural equality; AAA advisor; config; advisory mode only.

Phase 2 — Runtime Signals: per-test coverage (CAR), mock assert counts; BIS scoring & terminal summary + JSON.

Phase 3 — Duplicates & Contracts: AST LSH clustering, dynamic coverage clustering, parametrization & fixture suggestions; BRS roll-up + SARIF.

Phase 4 — Classifier & PR polish: optional ML scorer; GitHub Actions annotations spotlight “Top HOW offenders.”

If you want, I can turn this into a starter repo layout (folders + stub modules + pyproject.toml + sample persona strategies) so you can drop it into pytest-drill-sergeant and start filling in detectors.
