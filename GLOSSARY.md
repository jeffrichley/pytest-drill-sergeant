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

**Category marker**:
A pytest marker that classifies a test by kind (e.g. unit, integration, e2e) so whole categories can be selected or skipped.
_Avoid_: Test type, tag

**Level**:
How a check's findings count: `fail` (they fail the run), `warn` (reported, the run's result unchanged) or `off` (not reported). Each check has a default level.
_Avoid_: Severity

**Voice**:
The drill-sergeant persona in which findings are delivered: snarky in tone, precise in content.
_Avoid_: Persona, personality

**Waiver**:
A recorded, reasoned exemption that silences one finding (or one check for a scope), made deliberately and visible to reviewers.
_Avoid_: Suppression, ignore, noqa

**Agent guide**:
The instructions that teach a coding agent the checks before it writes tests, so it avoids failure modes instead of learning them from findings.
_Avoid_: Agent docs, prompt, instructions file
