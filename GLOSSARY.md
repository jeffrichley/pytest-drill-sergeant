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
The part of a pytest run's output, after the test results, where the plugin reports the run's findings: at most `drill_sergeant_max_findings` of them, then a count of the rest. The CLI shows every finding.
_Avoid_: Report summary, findings item

**Voice**:
The drill-sergeant persona in which findings are delivered: snarky in tone, precise in content.
_Avoid_: Persona, personality

**Waiver**:
A recorded, reasoned exemption that silences one finding (or one check for a scope), made deliberately and visible to reviewers.
_Avoid_: Suppression, ignore, noqa

**Agent guide**:
The instructions that teach a coding agent the checks before it writes tests, so it avoids failure modes instead of learning them from findings.
_Avoid_: Agent docs, prompt, instructions file
