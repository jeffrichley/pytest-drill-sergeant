# Pytest Drill Sergeant

A guardrail that catches the ways AI coding agents write bad tests, and reports them loudly enough that the agent has to fix them.

## Language

**Failure mode**:
A recurring way that AI-written tests go wrong (e.g. copy-pasted setup instead of a fixture, asserting nothing meaningful, brittle string matching).
_Avoid_: Anti-pattern, test smell (smell is a kind of check)

**Check**:
One deterministic detection of a single failure mode.
_Avoid_: Rule, validator, detector, analyzer

**Kind**:
What a check's failure mode costs: a defect, a smell or a convention. Each check has one, and it sets the highest default level the check can have (ADR 0001).
_Avoid_: Category (that's a category marker), type, severity

**Defect**:
The kind of a check whose failure mode leaves a test unable to catch a bug, cheating, or failing at random. Its default level can be `fail`.
_Avoid_: Bug, error

**Smell**:
The kind of a check whose failure mode leaves a test working but costing later: hard to read, broken by harmless refactors, or duplicated. Its default level is at most `warn`.
_Avoid_: Code smell, style issue

**Convention**:
The kind of a check that enforces a house rule some projects follow, such as AAA comments (DS108) or category markers (DS901). It is off by default; a project opts in.
_Avoid_: Style rule, house style

**Finding**:
One occurrence of a failure mode in a specific test, reported by a check. A finding names where it is, as a test's name would be: a class for a mark on the class, a function in production code, and `<module>` outside all of them, as for a skip mark in the module's `pytestmark` or a test file too long (the one failure mode of a whole file).
_Avoid_: Violation, error, issue, warning

**Real assertion**:
Anything in a test that can fail it on the outcome it checks: an `assert` of anything but a truthy constant or non-empty tuple, `pytest.raises`, `pytest.warns`, `pytest.deprecated_call` or `pytest.fail`, an `assert*` call (a mock's `assert_called_once_with`, `self.assertEqual`, `assert_frame_equal`), a call made through an assertion library, known by the file's imports (a pytest-check helper such as `check.equal`, a matcher on Playwright's `expect(...)`), or `raise AssertionError`; or a call to a function in the test tree whose body holds one, at any depth (a helper in the file or imported, a method reached through `self`, `cls` or `super()`, a name bound to one such as `partial(_check, ...)`, or a helper calling its own parameter when the call passes it an `assert*` function or such a function). A method on an object another call returned is never followed. A call to a function imported from a third-party package, a module found neither under the project nor in the standard library (pytest aside, whose functions are known), is code drill-sergeant can't see, so it may be one.
_Avoid_: Meaningful assertion, check (a check is drill-sergeant's)

**Test tree**:
The modules a test's calls are followed into for its real assertions: the run's test files, every `conftest.py`, and the modules in or below a directory that holds one of the run's test files, minus production code. In a flat layout, the production modules beside the tests are in it. An import is looked for under each directory above the importing file, nearest first, and the `src/` in each, up to the project root.
_Avoid_: Test suite (the tests alone), test package

**Weak assertion**:
An `assert` that holds for almost any value, wrong ones included: a bare name's truthiness, `is not None`, `isinstance` against builtins only (`dict`, `(int, float)`), `hasattr`, `callable`, `>= 0`, or a length that is merely non-zero. `isinstance` against a project or library class is not weak: there the type is the behaviour. Nor is the truthiness of a name bound to a filtered comprehension, which asks whether anything matched, as `x in y` does.
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
A skip that happens on every run: `pytest.mark.skip`, `skipif()` with no condition or on a truthy constant, or `pytest.skip(...)` as a statement of a test's own body under no condition.
_Avoid_: Disabled test

**Opt-out**:
An unconditional skip on a test method, by a mark on the method or a `pytest.skip(...)` in its own body, where the method overrides a test that a base class of its class defines: a `def` of the same name that pytest collects, in a base the test tree shows, followed through the classes around it and the file's imports. The first base that binds the name, depth first, decides; one that binds it to anything else (a fixture, `test_x = None`) hides the test. The base's test still runs for every other subclass, so DS402 doesn't report it; DS401 still asks for its reason. A base outside the test tree (third-party, the standard library, a module not found) shows nothing, so a skip under it is no opt-out. Nothing about it is read from the skip's reason or a name.
_Avoid_: Override skip, inherited skip

**Setup**:
A test's statements before the first one that holds a real assertion, its docstring aside.
_Avoid_: Arrange block, preamble

**Act**:
A statement of a test that is a bare call or `await` made for its effect, not an assertion, output known from the code (`print()`, `logging`) or a method of a pytest built-in fixture the test takes (`caplog.clear()`); cleanup is one. An assignment from a call sets up or reads a result, so it isn't one. For DS103, a bare call into a test-tree function that holds a real assertion is an assertion, and a bare call into a third-party package may assert, so neither is an act; DS104 doesn't follow calls yet. The act-and-assert order checks (DS103, DS104) count acts; DS102 asks a wider question, whether a test runs code under test at all, and never calls what it counts an act.
_Avoid_: Exercise step, when step

**Deliberate repeat**:
A loop in a test that runs the same pass a fixed number of times on purpose: `for _ in range(2)`, Python's own `range` (by the file's bindings) over a positive whole number written out, whose body never reads its target and carries nothing from one pass to the next. Every pass checks the same outcome, so DS107 leaves it alone.
_Avoid_: Retry loop (a retry stops early), parametrize

**AAA comment**:
A comment alone on its line that heads a section of a test: `# Arrange`, `# Act`, `# Assert`, or `# Act and assert` for both, alone or followed by `:` or a dash and any text. It heads the statements below it, up to the next one. Only the opt-in AAA comment check (DS108) reads them.
_Avoid_: Section marker, given/when/then

**Fingerprint**:
A short, stable digest of what one or more statements say: the same for statements that read alike wherever they stand, different for any change of name, literal or structure. Comments and layout don't change it.
_Avoid_: Hash (of a file), signature

**Shape**:
The fingerprint of statements with every name and literal blanked: alike for tests that differ only in their names and values.
_Avoid_: Skeleton, structure hash

**Per-file analysis**:
The step that reads one test file, and the modules of the test tree its tests' calls are followed into, and gives that file's findings and its per-file summary; the same bytes of those files and config give the same result.
_Avoid_: Local pass, file scan

**Per-file summary**:
What per-file analysis records of each test in a file for cross-file analysis: its name and line; the fingerprint, lines and bound names of each setup statement; the fingerprint and shape of its whole body, with the names and literals that shape blanks; and the fingerprint of its `def` line and decorators. Plain data, never the syntax tree.
_Avoid_: File index, digest

**Cache**:
Each test file's per-file analysis result, kept between runs in `d/drill-sergeant/` under pytest's cache directory and shared by the plugin and the CLI. A file is analysed again only when its key changes: the hash of its bytes, drill-sergeant's own code, or a config option per-file analysis reads (thresholds, category markers, source dirs, inline waivers), or its declared dependencies; or when a module of the test tree its analysis followed, or looked for there, or a production module it read a definition in, has changed, appeared, gone or left the test tree since. Levels, mode and per-file ignores apply after it, so changing them reuses every entry. Cross-file analysis always reruns, from the cached summaries.
_Avoid_: Memo, store

**Cross-file analysis**:
The step, after per-file analysis of every file in the run, that compares the per-file summaries, never the files, to find what is repeated across tests, in one file or many.
_Avoid_: Global pass, project analysis

**Mock**:
A test double made by `unittest.mock` or a pytest-mock fixture such as `mocker` (`Mock()`, `create_autospec`, `patch`), as the file shows it: made in the test, handed in by a `patch` decorator, or reached from one. A parameter named for a pytest-mock fixture is one only when pytest-mock is a declared dependency and the test sees no fixture of that name defined (or brought in by an import other than pytest-mock's, or a `*` import) in its module, a class around it or a `conftest.py` from its directory up to the config root. A name such as `mock_db` never makes a value one.
_Avoid_: Stub, fake (a fake is a working substitute, not a mock)

**Declared dependency**:
A package a test file's project names as one, in its directory or a directory above it up to the config root, or, when the config root holds no `pyproject.toml`, on up to the nearest directory that does: in `pyproject.toml` (`[project]` dependencies and optional dependencies, `[dependency-groups]`, `[tool.uv]` dev-dependencies, PDM's dev-dependencies, Hatch's environment dependencies, Poetry's dependency tables) or in a `.txt` whose name holds `requirements` or one in `requirements/`, its name normalised as PEP 503 does. Read from the files, never from what is installed, so the plugin and the CLI agree.
_Avoid_: Requirement, installed package

**Stand-in**:
A function, class or lambda a test defines and hands to the code under test without calling it itself, such as a slow callback passed in or a `side_effect`. What runs inside it is the stand-in's behaviour, not the test's.
_Avoid_: Fake (a fake is a working substitute), helper (a helper is one the test calls)

**Mock setup**:
A statement in a test that makes, patches in or configures a mock: `repo = mock.Mock(spec=Repo)`, a `patch` decorator or `with` item, `repo.get.return_value = ...`.
_Avoid_: Mock configuration, arrange

**Category marker**:
A pytest marker that classifies a test by category (e.g. unit, integration, e2e) so whole categories can be selected or skipped.
_Avoid_: Test type, tag

**Level**:
How a check's findings count: `fail` (they fail the run), `warn` (reported, the run's result unchanged) or `off` (not reported). Each check has a default level, the lower of what its kind allows and what its proof allows: off until the check is proven, and never above `warn` for a smell or above `off` for a convention.
_Avoid_: Severity

**Proven**:
Said of a check whose findings, over a fresh hand-judged sample of real suites, hold few enough false positives for a level: none allows `fail`; under 15%, with each remaining one waived, allows `warn`; 15% or more keeps it off. Only a proven check is on by default, at the lower of that level and its kind's highest; the rest come on one by one as each is proven.
_Avoid_: Stable, trusted

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
A configured number a check measures against, such as the most lines of code a test may have.
_Avoid_: Limit, setting

**Findings section**:
The part of a pytest run's output, after the test results, where the plugin reports the run's findings: at most `drill_sergeant_max_findings` of them, then a count of the rest, then a tally by level and of waived findings. The CLI shows every finding.
_Avoid_: Report summary, findings item

**Voice**:
The drill-sergeant persona in which findings are delivered: snarky in tone, precise in content.
_Avoid_: Persona, personality

**Waiver**:
A `# drill: waive DS### -- <reason>` comment that silences the named check's findings on its line, or anywhere in a test when it sits on the test's `def` line (through the `):` a wrapped signature closes on; never a decorator's line): a reasoned exemption, made deliberately and visible to reviewers. It must name the code and give a reason, or it waives nothing and is itself a finding. Every run tallies the findings waived.
_Avoid_: Suppression, ignore, noqa

**Agent guide**:
The instructions that teach a coding agent the checks before it writes tests, so it avoids failure modes instead of learning them from findings.
_Avoid_: Agent docs, prompt, instructions file

**Agent Skill**:
The `SKILL.md` that `drill-sergeant agent-guide --install` writes, holding the full agent guide where a repo's agents look for skills: `.agents/skills/drill-sergeant/` beside AGENTS.md, `.claude/skills/drill-sergeant/` beside CLAUDE.md. The install also adds a block to the AGENTS.md or CLAUDE.md, marked with drill-sergeant's version, that points at the skill; a rerun replaces only that block.
_Avoid_: Skill file, snippet (for the block)
