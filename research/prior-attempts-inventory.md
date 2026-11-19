# Inventory of the two earlier attempts

Resolves the wayfinder ticket **Inventory the two earlier attempts**. This is a throwaway research branch and is never merged.

Sources:
- **A.** current `main` (v0.4.0), about 1,900 source lines
- **B.** the tag `archive/2026-02-13/rewrite/main`, about 730 KB of source

Verdicts are judged against the destination: a deterministic guardrail for agent-written tests, with findings in the pytest stream, written for an agent reader, in the drill-sergeant voice.

## Bottom line

Keep very little code. Mine the ideas.

| Carry forward | From | Form |
|---|---|---|
| A "no assertions" check (DS401) | B `car_calculator.py` | Idea. It needs to recognize `pytest.raises` and mock asserts. It's the most on-target check in either tree, and it was buried outside the default pipeline. |
| Private-access check (DS301) | B | AST shell. Exempt dunders and the test's own helpers; it's noisy today. |
| Mock-overspec check (DS102) | B | AST shell. The logic is shallow: the allowlist matches variable names and tests inside `class Test*` are never analyzed. |
| Structural-equality / brittle-string check (DS306) | B | AST shell. Restrict it to `assert` and `==` contexts; today it flags every `str()` / `repr()`. |
| Fixture extraction, parametrization suggestion, SimHash static clones | B `planning/03_analysis_algorithms.md` §2–4 | **Specs only. Never implemented.** These are the closest match to "copy-pasted setup instead of a fixture". |
| Hook skeleton: analyze each file once (cached), report in `pytest_terminal_summary`, set the exit status in `sessionfinish` | B `plugin/hooks.py` | Shape only. B never failed the run and swallowed every exception. |
| A slim `Finding` (check id, file:line, message, suggestion) | B `core/models.py` | Slimmed. Drop confidence, fixable and fingerprint. |
| The rule-id catalog (DS-codes) | B `core/rulespec.py` | Mine the ids and names. Drop the scoring linkage. |
| A small check Protocol plus a list registry | A `validators/base.py`, `registry.py` | The idea. Rename to "check". |
| Voice: README tone, a dozen good drill-sergeant lines | A README, B `personas/drill_sergeant.py` | Mine, and strip the contaminated lines. |
| Failure-Catalog doc format | A `docs/Failure-Catalog.md` | The format, not the content. |
| A fixture corpus of bad tests | B `tests/unit/test_ultimate_coverage.py`, `test_final_push.py`, `test_tiny_coverage.py`, `test_coverage_boost.py` | Coverage-padding tests (`assert x is not None` on imports) are a ready-made set of bad examples for the guardrail. |

## A. Current `main` (v0.4.0)

132 tests pass. Real coverage of the function bodies is about 75–90%; the reported 64% undercounts because of import timing under pytest11.

| Component | What / how | Verdict |
|---|---|---|
| Marker check (path-based auto-detection) | Fails tests with no marker; infers one from the directory. Static. Duplicated across the collection hook and the validator. | **Drop.** Project taxonomy, not something agents get wrong. |
| Marker writer | Rewrites test source during collection, **on by default**, using line-based text surgery. Fragile with docstrings. | **Drop.** A guardrail reports, it doesn't edit files mid-run under an agent's in-flight edits. Put the fix in the finding's suggestion instead. |
| AAA comment check | Regex for `# Arrange - …` etc. via `inspect.getsource`. 261 lines, well tested. | **Drop as written.** It rewards surface compliance, since an agent can sprinkle the comments over a test that proves nothing. The useful core (there is an act and a real assert; no assert before the act) is better done in the syntax tree. |
| File-length check | Line count against a limit. Runs once per test item, so N identical findings per file. | **Rework or drop.** A weak stand-in for copy-paste. |
| `config.py` (4-layer precedence), `config_schema.py`, `utils/helpers.py` (529 lines) | env > ini > `[tool.drill_sergeant]` > defaults; rebuilt and `pyproject.toml` re-parsed for every test. | **Drop.** Contradicts "deliberately minimal". |
| `pytest_options.py` | `parser.addini` registrations. | **Rework.** Right pattern, far fewer options. |
| `error_reporter.py` | `pytest.fail()` with emoji blocks. Not in the voice. | **Rework.** Located, terse, voice on top. |
| `plugin.py` | Runs checks in `pytest_runtest_setup` and fails *that test*. | **Rework.** Per-test setup failures hide real results; collect findings and report them at session level. |

## B. Archived rewrite: checks

Only five analyzers were in the default pipeline: aaa_comments, duplicate_tests, mock_overspec, private_access, structural_equality.

| Component | Failure mode | How | Quality | Verdict |
|---|---|---|---|---|
| private_access_detector (406, DS301) | Reaching into internals | AST | Dunders flagged as private (a test enshrines it); `self._x` flagged | Rework |
| mock_overspec_detector (240, DS102) | Asserting how mocks were called | AST, more than 3 `assert_called*` | Hard-coded threshold (TODOs); misses class-based tests | Rework |
| structural_equality_detector (357, DS306) | Brittle `__dict__` / `repr` / `str` assertions | AST | Flags every `str()` / `repr()` anywhere | Rework |
| aaa_comment_detector (531, DS302) | Missing AAA comments | Line scan | Finished, but style | Drop, or opt-in |
| car_calculator (356, DS401/402) | No assertions / too many | AST + coverage | CAR rewards fewer assertions (backwards); not in the pipeline | Drop CAR, salvage DS401 |
| duplicate_test_detector (211, DS201) | Duplicate tests | Compares test **names** | Every finding at line 1 | Drop |
| clone_detector (685) | Near-duplicate tests | Weighted coverage + "structure" (which includes the function name) | `analyze_file` placeholder | Drop the code, keep the idea |
| coverage_collector (1634), coverage_signature (409) | Per-test coverage | Imports and calls test functions directly, so no fixtures | Breaks on fixtures; TODOs | Drop |

## B. Archived rewrite: scoring

BIS, BRS, dynamic BIS, feature extractor and `scoring_models.py`: **drop all of it.** A score of 72 doesn't tell an agent what to change. Bugs found:
- per-test BIS is computed from the whole file's findings
- BRS invents its test count
- `scoring_models.py` is dead code kept alive by a coverage-padding test

## B. Archived rewrite: voice / personas

- **Mechanism:** `random.choice(templates)` per message type, so output isn't deterministic.
- **Wiring:** per-check templates were badly wired; mock-overspec templates could never be reached.
- **The voice drops the finding:** no template includes `{finding_message}`, so the agent learns nothing it can act on.
- **Hook bugs:** the voice is written even for passing tests; unrelated failures get a dummy DS999.
- **Contamination:** the drill-sergeant templates are polluted with pirate, butler and coach lines.
- **Verdict:**
  - Rework strategy and drill_sergeant: one deterministic message per check, always carrying the fact and the fix.
  - Drop snoop_dogg, manager and models.

Good lines worth keeping (verbatim):
- "WHAT IS THIS AMATEUR HOUR?! Test {test_name} is importing PRIVATE modules! DO YOU SNEAK INTO THE SERGEANT'S QUARTERS?!"
- "Test {test_name} is calling PRIVATE methods! That's like calling the SERGEANT by his first name!"
- "Test {test_name} is a MOCK-UP of incompetence! STOP micromanaging the internals, RECRUIT!"
- "Test {test_name} is micromanaging mocks like a control freak! Test the OUTCOME, not the process, maggot!"
- "Test {test_name} is a DISASTER! Fix this MESS before I make you drop and give me twenty!"
- "FINALLY! Test {test_name} passes muster!"
- "Test {test_name} - ACCEPTABLE! You're learning, maggot!"

## B. Archived rewrite: infrastructure

About 14k lines, much of it never wired up. The only registered entry point was `plugin.hooks`.

| Component | Lines | Verdict |
|---|---|---|
| Typer CLI (`lint`, plus `maggot` / `sorry-excuse` aliases) | ~1,090 | Drop. The destination is the pytest stream. |
| **Nine config modules** (profiles, registry, "enhanced" validator) | ~4,000 | Drop. The clearest over-engineering. |
| analysis_pipeline, analysis_result, error_handler (recovery strategies), file_discovery (gitignore parsing), logging_utils | ~1,930 | Drop. A loop over checks is enough, the tool should crash loudly, and pytest collection already decides which files are tests. |
| reporting (JSON, SARIF, templates, output manager) | ~1,630 | Drop for v1. One small optional writer could come back later. |
| LSP server | ~835 | Drop |
| Plugin framework (base, factory, extensibility, discovery, hot reload): **never used** | ~1,800 | Drop |
| Coverage plumbing (coverage_hooks, pytest_cov_integration, coverage_storage) | ~1,350 | **Drop. Broken.** It treats cumulative session coverage as per-test and re-runs tests outside pytest. A runtime duplicate check should be written fresh on coverage.py **dynamic contexts** (`switch_context(nodeid)` / `--cov-context=test`, read back via `contexts_by_lineno`). |

There's also top-level clutter in the tag: committed report output, self-congratulating summary docs, 16 planning docs plus chat logs, `.cursor/rules`, `examples/` and `vscode-extension/`.
