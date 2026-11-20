# Pytest Drill Sergeant

A guardrail that catches the ways AI coding agents write bad tests, and reports them loudly enough that the agent has to fix them.

## Language

**Failure mode**:
A recurring way that AI-written tests go wrong (e.g. copy-pasted setup instead of a fixture, asserting nothing meaningful, brittle string matching).
_Avoid_: Anti-pattern, test smell

**Check**:
One deterministic detection of a single failure mode.
_Avoid_: Rule, validator, detector, analyzer

**Finding**:
One occurrence of a failure mode in a specific test, reported by a check.
_Avoid_: Violation, error, issue, warning

**Real assertion**:
Anything in a test that can fail it on the outcome it checks: an `assert` of anything but a truthy constant or non-empty tuple, `pytest.raises`, `pytest.warns`, `pytest.deprecated_call` or `pytest.fail`, an `assert*` call (a mock's `assert_called_once_with`, `self.assertEqual`, `assert_frame_equal`), or `raise AssertionError`.
_Avoid_: Meaningful assertion, check (a check is drill-sergeant's)

**Weak assertion**:
An `assert` that holds for almost any value, wrong ones included: a bare name's truthiness, `is not None`, `isinstance`, `hasattr`, `callable`, `>= 0`, or a length that is merely non-zero.
_Avoid_: Loose assertion, shallow assertion

**Tautological assertion**:
An `assert` that can't fail whatever the code under test does: it compares an expression with itself, compares only values the test wrote itself, or multiplies the result by zero.
_Avoid_: Trivial assertion, always-true assertion

**Mirror assertion**:
An `==` whose expected side is taken from the code under test: the same call on both sides, directly or through names the test bound to it. Names never matter: `first == second`, each bound to the same call, is one just as `result == expected` is.
_Avoid_: Self-check, circular assertion

**Production code**:
The code under test, as opposed to the tests: the `.py` files under `drill_sergeant_source_dirs`, or under `src/` when that is empty. Only the special-casing check (DS403) reads it, in full every run.
_Avoid_: Source (alone), app code, implementation

**Unconditional skip**:
A skip that happens on every run: `pytest.mark.skip`, `skipif` on a truthy constant, or `pytest.skip(...)` as a statement of a test's own body under no condition.
_Avoid_: Disabled test

**Setup**:
A test's statements before the first one that holds a real assertion, its docstring aside.
_Avoid_: Arrange block, preamble

**Fingerprint**:
A short, stable digest of what one or more statements say: the same for statements that read alike wherever they stand, different for any change of name, literal or structure. Comments and layout don't change it.
_Avoid_: Hash (of a file), signature

**Shape**:
The fingerprint of statements with every name and literal blanked: alike for tests that differ only in their names and values.
_Avoid_: Skeleton, structure hash

**Per-file analysis**:
The step that reads one test file on its own and gives that file's findings and its per-file summary; the same file bytes and config give the same result.
_Avoid_: Local pass, file scan

**Per-file summary**:
What per-file analysis records of each test in a file for cross-file analysis: its name and line; the fingerprint, lines and bound names of each setup statement; and the fingerprint and shape of its whole body. Plain data, never the syntax tree.
_Avoid_: File index, digest

**Cross-file analysis**:
The step, after per-file analysis of every file in the run, that compares the per-file summaries, never the files, to find what is repeated across tests, in one file or many.
_Avoid_: Global pass, project analysis

**Mock**:
A test double made by `unittest.mock` or a pytest-mock fixture such as `mocker` (`Mock()`, `create_autospec`, `patch`), as the file shows it: made in the test, handed in by a `patch` decorator, or reached from one. A name such as `mock_db` never makes a value one.
_Avoid_: Stub, fake (a fake is a working stand-in, not a mock)

**Mock setup**:
A statement in a test that makes, patches in or configures a mock: `repo = mock.Mock(spec=Repo)`, a `patch` decorator or `with` item, `repo.get.return_value = ...`.
_Avoid_: Mock configuration, arrange

**Category marker**:
A pytest marker that classifies a test by kind (e.g. unit, integration, e2e) so whole categories can be selected or skipped.
_Avoid_: Test type, tag

**Level**:
How a check's findings count: `fail` (they fail the run), `warn` (reported, the run's result unchanged) or `off` (not reported). Each check has a default level.
_Avoid_: Severity

**Mode**:
The run-wide setting over every level: `fail` (each check at its level), `warn` (every finding reported as `warn`) or `off` (no check runs). Set by `drill_sergeant_mode`.
_Avoid_: Global level, strictness

**Family**:
The checks whose codes share a prefix (DS1xx structure, DS2xx assertions, and so on). A family prefix (`DS1` or `DS1xx`) in config covers every check in it; the most specific entry wins.
_Avoid_: Category (that's a category marker), group

**Per-file ignore**:
A config entry (`glob: codes`) that keeps the named checks off the files matching the glob, relative to the config file's directory. Unlike a waiver it lives in config and isn't tallied.
_Avoid_: Exclude, waiver

**Threshold**:
A configured number a check measures against, such as the most lines a test may have.
_Avoid_: Limit, setting

**Findings section**:
The part of a pytest run's output, after the test results, where the plugin reports the run's findings: at most `drill_sergeant_max_findings` of them, then a count of the rest, then a tally by level and of waived findings. The CLI shows every finding.
_Avoid_: Report summary, findings item

**Voice**:
The drill-sergeant persona in which findings are delivered: snarky in tone, precise in content.
_Avoid_: Persona, personality

**Waiver**:
A `# drill: waive DS### -- <reason>` comment that silences the named check's findings on its line, or anywhere in a test when it sits on the test's `def` line: a reasoned exemption, made deliberately and visible to reviewers. It must name the code and give a reason, or it waives nothing and is itself a finding. Every run tallies the findings waived.
_Avoid_: Suppression, ignore, noqa

**Agent guide**:
The instructions that teach a coding agent the checks before it writes tests, so it avoids failure modes instead of learning them from findings.
_Avoid_: Agent docs, prompt, instructions file
