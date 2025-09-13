Skip to content
Chat history

You said:
Here is a really big problem I get with Ai coders, they want to test HOW something works instead of WHAT it does.
ChatGPT said:
Ohhh yes — I know exactly what you mean.

AI coders (and sometimes junior human devs too) fall into the trap of writing tests that lock in implementation details instead of observable behavior. A couple examples:

Testing how

“Does this function call sorted() internally?”

“Does it use a loop vs. a comprehension?”

“Does this class have a private_helper() method that gets invoked?”

Testing what

“Does the function return the list sorted correctly?”

“Do I get the same outputs for the same inputs, regardless of internal tricks?”

“Does the public API guarantee hold true under edge cases?”

The what approach makes your tests stable and valuable because you can refactor all day long without rewriting the test suite. The how approach makes tests brittle — you change an internal detail and suddenly your test suite screams, even though the public contract never broke.

Some tricks I use to keep tests focused on what:

Golden rule: Only test public interfaces, never private methods/attributes.

Property-based testing: Great for “what” — e.g. f(f(x)) == f(x) or “output length always matches input length.”

Black-box mindset: Pretend you don’t know the implementation. Just feed inputs, observe outputs, and assert behaviors.

AAA comments (Arrange, Act, Assert): Forces discipline: arrange state, act, assert result. If you catch yourself asserting calls instead of results, you’re probably testing “how.”

Mutation testing: Helps reveal if your “what” assertions are strong enough without over-specifying “how.”

Do you want me to sketch out some heuristics (almost like lint rules) that your plugin could enforce to catch when an AI (or human) coder is drifting into “how” territory instead of “what”?

You said:
Please put together a detailed way we can detect this using our pytest framework. What kind of algos can we use
ChatGPT said:

Thought for 12s
Totally. Let’s build this into your pytest plugin as a set of detectors that each raise a “HOW-smell” signal and roll up into a Behavior Integrity Score (BIS). Below is a concrete, code-ready plan with algorithms you can implement.

Detectors & Algorithms (WHAT vs HOW)
1) Private-Surface Access (AST)
Smell: Tests touch private members (_foo, __bar) or private modules.
Signal: Strong HOW.
Algo: Parse each test file with ast; flag Attribute/Name nodes with identifiers starting _ that resolve to the SUT package, and imports like from pkg._internal import ….

Sketch:

# conftest.py (or your plugin)
import ast, pathlib

class PrivateAccessVisitor(ast.NodeVisitor):
    def __init__(self, sut_top_pkg: str):
        self.offenses = []
        self.sut_top_pkg = sut_top_pkg

    def visit_ImportFrom(self, node):
        if node.module and node.module.startswith(self.sut_top_pkg + "._"):
            self.offenses.append(("private-import", node.lineno, node.module))
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # track attr names like obj._private
        if isinstance(node.attr, str) and node.attr.startswith("_"):
            self.offenses.append(("private-attr", node.lineno, node.attr))
        self.generic_visit(node)

def scan_private_access(path: pathlib.Path, sut_top_pkg: str):
    tree = ast.parse(path.read_text())
    v = PrivateAccessVisitor(sut_top_pkg)
    v.visit(tree)
    return v.offenses
2) Mock/Spy Over-Specification (Runtime + AST)
Smell: Assertions on call sequences, exact call counts, or specific helper names.
Signal: Moderate→Strong HOW.
Algo A (AST): Detect assert_has_calls, assert_called_once, assert_called_with on objects created via unittest.mock or pytest-mock.
Algo B (Runtime): Wrap pytest_runtest_call; introspect failures and captured logs; count uses of Mock assert methods.

Sketch (AST):

MOCK_ASSERTS = {"assert_called_once", "assert_called_with", "assert_has_calls", "assert_any_call"}
class MockAssertVisitor(ast.NodeVisitor):
    def __init__(self): self.count = 0
    def visit.Attribute(self, node):
        if node.attr in MOCK_ASSERTS: self.count += 1
        self.generic_visit(node)
Heuristic: Allow mocks at system boundaries (I/O, HTTP, time, randomness). Add allowlist via config (e.g., allowed_mocks = ["requests.Session", "boto3.*", "time.*", "random.*"]). Penalize mocking internal functions/classes.

3) Call-Graph Expectation (AST)
Smell: Tests assert that specific internal functions were invoked (patch paths referencing internal modules).
Signal: Strong HOW.
Algo: AST search for patch("mypkg._internal...") or mocker.patch("mypkg.module.helper") where helper is not exported in __all__.

You can optionally read the package’s __all__ at import time and penalize patch targets not in it.

4) Snapshot of Intermediates (AST)
Smell: Snapshots (e.g., pytest-approvaltests, syrupy) of private or intermediate objects.
Signal: Moderate HOW.
Algo: Detect calls to snapshot.assert_match or verify(...) where the expression references private attrs or non-public types from SUT.

5) Over-specific Exception Assertions (AST)
Smell: Asserting exact message text of exceptions rather than type/contract.
Signal: Weak→Moderate HOW.
Algo: Find pytest.raises contexts with match= that’s long or highly specific (e.g., >40 chars or with many punctuation tokens).
Rule: Prefer asserting exception type + key token(s), not full wording.

6) Structural Equality on Internal Types (AST)
Smell: assert obj.__dict__ == {...} or asdict() of internal dataclasses, or comparing repr(obj) to a string.
Signal: Strong HOW.
Algo: Detect comparisons where LHS or RHS uses .__dict__, vars(), dataclasses.asdict, or repr() of SUT objects.

7) Behavior-vs-Implementation Classifier (Rule-Based → Optional ML)
Smell: Aggregate pattern of the above.
Signal: Overall.
Algo: Engineer features per test:

uses_private_imports, private_attrs_count

mock_assert_count, patched_internal_count

exception_message_len, structural_compare_count

public_api_assert_count (positive signal): assertions against return values or public protocol.
Compute a score with weighted sum:

BIS = 100
      - 15*private
      - 10*mock_calls
      - 15*patched_internal
      - 8*structural
      - 5*exc_msg_overspec
      + 8*public_api_asserts_clamped
Thresholds: BIS ≥ 85 = Good, 70–84 = Caution, <70 = Drifting into HOW.

You can later replace the weights with a simple logistic regression trained on labeled tests. Keep the features; swap the scorer.

8) Duplicate/Isomorphic Test Detector (LSH)
Smell: AI writes many near-identical tests (different names, same assertions).
Signal: Quality drag (not strictly HOW, but related).
Algo:

Normalize AST of each test (strip literals/ids; keep structure).

Build shingles of node types (n-grams of AST node labels).

Compute MinHash signatures; use LSH to bucket near duplicates.

Flag clusters with size ≥ K and Jaccard ≥ τ (e.g., 0.85).

This deters “testing the same HOW repeatedly”.

9) Fixture Overreach (AST + Runtime)
Smell: Fixtures inject internal state or patch internals globally.
Signal: Moderate HOW.
Algo: Scan conftest.py fixtures for:

Patching internal helpers at autouse=True.

Creating objects via private constructors.
At runtime, track which fixtures are used by low BIS tests and surface as contributors.

10) Coverage-to-Assertion Ratio (Runtime)
Smell: Tests touch many lines but assert few public outcomes (likely poking internals).
Signal: Moderate HOW.
Algo: With coverage.py, per test (use coverage.Coverage + pytest_runtest_call), compute:

Lines covered in SUT

Count of assert statements in the test body (AST)
Compute CAR = covered_lines / (assert_count + 1); high CAR with low BIS ⇒ suspicious.

Plugin Hook Plan (pytest)
Collection:

pytest_collect_file → run AST scanners on test files; store per-test features in a registry.

pytest_collection_modifyitems → attach metadata (features) to Item.

Execution:

pytest_runtest_setup/call → measure coverage per test (use dynamic contexts); capture mock assert calls (optionally monkeypatch Mock assert methods to increment counters).

pytest_assertrepr_compare → when string-matching exceptions occur, record the pattern length.

Reporting:

pytest_terminal_summary → show:

Behavior Integrity Score per test/class/module

Top offenders and their reasons

Battlefield Readiness Score section:

% tests BIS≥85

Duplicate test clusters

Mock/patch hotspots

CAR distribution

Optional --drill-sergeant-json=out.json with a machine-readable report.

Configuration (pytest.ini / toml)
[pytest]
addopts = -q
# drill-sergeant
ds_sut_top_pkg = mypkg
ds_allow_mock_targets =
    requests.*
    boto3.*
    time.*
    random.*
ds_bis_threshold_warn = 80
ds_bis_threshold_fail = 65
ds_dup_jaccard = 0.85
ds_dup_min_cluster = 3
Provide --ds-fail-on-how to fail build when BIS below threshold or private access found.

Provide --ds-print-examples to show a short “rewrite suggestion” for each offense.

Example: Feature Extraction per Test (wire-up)
import ast, inspect, types, coverage
from collections import defaultdict

TEST_FEATURES = defaultdict(lambda: {
    "private":0, "mock_calls":0, "patched_internal":0, "structural":0,
    "exc_msg_chars":0, "public_api_asserts":0, "covered_lines":0, "asserts":0
})

def compute_bis(feat):
    return max(0, min(100,
        100
      - 15*feat["private"]
      - 10*feat["mock_calls"]
      - 15*feat["patched_internal"]
      - 8*feat["structural"]
      - 5*(feat["exc_msg_chars"]//40)
      + 8*min(feat["public_api_asserts"], 5)
    ))

def pytest_collect_file(path, parent):
    if path.ext == ".py" and "test_" in path.basename:
        # run AST passes: private access, mock asserts, structural compares, asserts count
        tree = ast.parse(path.read_text())
        # ... visit with the visitors above, fill TEST_FEATURES keyed by test node names

def pytest_runtest_call(item):
    # start per-test coverage
    cov = coverage.Coverage(data_file=None, context="test:"+item.name)
    cov.start()
    item.ihook.pytest_pyfunc_call(pyfuncitem=item)  # run the test
    cov.stop()
    cov.save()
    # compute covered SUT lines for this test's context
    # ... set TEST_FEATURES[item.nodeid]["covered_lines"] = N
Public-API assertion heuristic: count assert comparing full return values or public attributes of the result variable(s); avoid counting equality against .__dict__/repr etc.

De-HOW Suggestions Generator (Optional)
For each offense, generate a targeted rewrite hint:

Private attribute access → “Assert the returned value or documented property exposed via the public API. If you need an invariant, capture it as a property test with Hypothesis.”

Mock call order → “Prefer asserting observable effect (e.g., file written, HTTP body sent) or state of the result. If interaction is the contract (e.g., retries), assert semantic outcome (N retries recorded) rather than exact call stack.”

Property-Based “WHAT” Boosts (positive signal)
Provide a decorator to bump BIS when used:

import pytest
from hypothesis import given, strategies as st

def behavior_contract(name):
    def deco(fn):
        fn.__behavior_contract__ = name
        return fn
    return deco

@behavior_contract("sort is idempotent")
@given(st.lists(st.integers()))
def test_sort_idempotent(xs):
    assert sorted(sorted(xs)) == sorted(xs)
During collection, detect __behavior_contract__ and add +10 to public_api_asserts.

Duplicate Test Finder (LSH sketch)
from datasketch import MinHash, MinHashLSH

def ast_shingles(tree):
    labels = [type(n).__name__ for n in ast.walk(tree)]
    return set(tuple(labels[i:i+4]) for i in range(len(labels)-3))

def cluster_tests(test_paths):
    lsh = MinHashLSH(threshold=0.85)
    sigs = {}
    for path in test_paths:
        tree = ast.parse(path.read_text())
        m = MinHash()
        for sh in ast_shingles(tree):
            m.update((",".join(sh)).encode())
        sigs[path] = m
        lsh.insert(path, m)
    # query clusters
    clusters = []
    seen = set()
    for p, m in sigs.items():
        if p in seen: continue
        bucket = set(lsh.query(m))
        if len(bucket) >= 3:
            clusters.append(sorted(bucket))
        seen |= bucket
    return clusters
How this fits your Battlefield Readiness Score
Add a “Behavior Focus” subsection:

BIS median / p10 / p90

% tests ≥ 85

Top HOW smells: private access (N), patched internals (N), call-order asserts (N)

Duplicate clusters: count + sample names

CAR histogram

Minimal Path to Green (Phased)
Phase 1 – Static Guards

Implement Detectors 1, 3, 5, 6 (AST) + config.

Emit warnings; --ds-fail-on-how opt-in.

Phase 2 – Runtime Signals

Coverage per test (CAR).

Count mock assert calls.

Report BIS; wire to terminal summary + JSON.

Phase 3 – Duplicates & Contracts

LSH duplicate clusters.

@behavior_contract decorator + Hypothesis encouragement.

Phase 4 – Classifier

Swap weighted BIS for simple ML (optional).

Add per-repo “Top HOW offenders” GitHub Action annotation.

If you want, I can turn this into a drop-in pytest-drill-sergeant module layout (with the visitors, hooks, config parsing, and a nice terminal report) so you can paste it straight into your repo.

You said:
What is SUT package
ChatGPT said:
Great question 👌

SUT = System Under Test.
It just means the codebase you are testing (your library, app, or module).

So when I wrote things like:

scan_private_access(path, sut_top_pkg="mypkg")
That sut_top_pkg is just the top-level package name of your project.

If your code lives under src/redwing_core/, then the SUT package is redwing_core.

If it’s src/algokit/, then the SUT package is algokit.

If it’s a single-file script, then you can treat the module name as the SUT.

The plugin needs to know this so it can tell the difference between:

You poking at your own internals (bad → HOW test)

You touching stdlib or third-party internals (different smell, sometimes allowed)

Would you like me to show you how to auto-detect the SUT package name from a pytest run (so you don’t have to hardcode it), or would you prefer it to be explicitly set in pytest.ini?



No file chosenNo file chosen
ChatGPT can make mistakes. Check important info.
