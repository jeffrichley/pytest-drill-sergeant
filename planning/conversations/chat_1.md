Skip to content
Chat history

You said:
I’m writing a purest plugin sweet that tries to squash the silly things ai coding agents do.
ChatGPT said:

Thought for 8s
Hey Jeff — Iris here. I’m guessing you meant a pytest plugin suite (cute typo: “purest plugin sweet” 🍬). Here’s a crisp blueprint to squash the most common “AI agent gremlins” before they ever reach CI.

Anti-Gremlin: a pytest plugin suite for AI-written code
What we’re targeting (the “silly things”)
Silent network calls (no timeouts, live internet in unit tests)

Hidden global state & nondeterminism (random seeds, time, env)

Filesystem pollution (writing outside tmp paths)

Flaky sleeps & fragile timing (time.sleep in tests)

No-ops & dead code (unused vars, unreachable branches)

Wildcard imports / implicit reexports

Missing type hints & sloppy exceptions (except:)

Hard-coded credentials / secrets

Long logs and snapshot noise

Slow tests with no markers

Unbounded subprocesses / shell calls

Mocking as implementation (over-mocking), brittle patch targets

Plugin suite layout
ai_guardrails/
  pyproject.toml
  src/ai_guardrails/__init__.py
  src/ai_guardrails/_config.py
  src/ai_guardrails/_net.py
  src/ai_guardrails/_fs.py
  src/ai_guardrails/_time.py
  src/ai_guardrails/_secrets.py
  src/ai_guardrails/_style.py
  src/ai_guardrails/_perf.py
  src/ai_guardrails/_snap.py
  src/ai_guardrails/plugin.py
  tests/
Key features (each is a small, focused hook)
1) No-Internet-by-default (with opt-in)
Block socket by default; allow with @pytest.mark.net only.

# src/ai_guardrails/_net.py
import socket, pytest

class _NoNet:
    def __init__(self): self._orig = socket.socket
    def __call__(self, *a, **kw): raise RuntimeError("Network disabled in tests. Use @pytest.mark.net.")

def enable_no_network():
    socket.socket = _NoNet()

def disable_no_network():
    # restore in teardown if needed
    from importlib import reload; reload(socket)

def pytest_runtest_setup(item):
    if "net" not in item.keywords:
        enable_no_network()
2) Determinism: seeds, frozen time, env hygiene
# src/ai_guardrails/_time.py
import os, random, numpy as np, pytest
from datetime import datetime
from freezegun import freeze_time

@pytest.fixture(autouse=True, scope="function")
def deterministic_env(monkeypatch):
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    random.seed(1337)
    try:
        np.random.seed(1337)  # if numpy present
    except Exception: pass

@pytest.fixture
def freeze_now():
    with freeze_time("2024-01-01 00:00:00"):
        yield datetime.utcnow()
3) Filesystem sandbox
Fail any write outside pytest’s tmp paths unless @pytest.mark.fs.

# src/ai_guardrails/_fs.py
import builtins, os, pytest
ALLOWED_PREFIXES = lambda tmpdir: {str(tmpdir), os.getcwd()}

@pytest.fixture(autouse=True)
def guard_writes(tmp_path, monkeypatch, request):
    if "fs" in request.keywords:
        yield; return
    _open = builtins.open
    def safe_open(p, *a, **k):
        if "w" in "".join(a) or k.get("mode", "").find("w")!=-1:
            if not any(str(p).startswith(pfx) for pfx in ALLOWED_PREFIXES(tmp_path)):
                raise RuntimeError(f"Write outside sandbox: {p}")
        return _open(p, *a, **k)
    monkeypatch.setattr(builtins, "open", safe_open)
    yield
4) Ban sleeps & enforce timeouts
# src/ai_guardrails/_perf.py
import time, functools, pytest

@pytest.fixture(autouse=True)
def ban_sleep(monkeypatch, request):
    if "timing" in request.keywords:
        yield; return
    def _no_sleep(seconds):
        raise AssertionError("time.sleep is banned in tests (use markers or fake timers).")
    monkeypatch.setattr(time, "sleep", _no_sleep)

def pytest_addoption(parser):
    parser.addoption("--max-test-seconds", action="store", type=float, default=5.0)

def pytest_runtest_call(item):
    import signal
    max_s = item.config.getoption("--max-test-seconds")
    def _handler(*_): raise TimeoutError(f"Test exceeded {max_s}s")
    signal.signal(signal.SIGALRM, _handler); signal.alarm(int(max_s))
5) Secret & credential scans (lightweight)
Regex scan of added/modified files in test session; block obvious API keys.

# src/ai_guardrails/_secrets.py
import re, pathlib, pytest
PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),                      # AWS Access Key
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"][\w-]{20,}"),
    re.compile(r"-----BEGIN (RSA|EC) PRIVATE KEY-----"),
]

def pytest_sessionstart(session):
    root = pathlib.Path(session.config.rootpath)
    offenders = []
    for p in root.rglob("*.py"):
        try: tx = p.read_text(encoding="utf-8", errors="ignore")
        except Exception: continue
        for pat in PATTERNS:
            if pat.search(tx): offenders.append(p); break
    if offenders:
        raise RuntimeError(f"Potential secrets found in: {', '.join(map(str, offenders[:5]))}")
6) Style/robustness lint (fast, in-plugin)
Quick AST checks for except:, wildcard imports, print in lib code, requests without timeout.

# src/ai_guardrails/_style.py
import ast, pathlib, pytest, re

REQ_NO_TIMEOUT = re.compile(r"requests\.(get|post|put|delete)\([^)]*?\)")

def _walk_py(root):
    for p in pathlib.Path(root).rglob("*.py"):
        yield p, p.read_text(encoding="utf-8", errors="ignore")

def pytest_collection_finish(session):
    root = session.config.rootpath
    problems = []
    for p, src in _walk_py(root):
        try: tree = ast.parse(src)
        except SyntaxError as e:
            problems.append((p, f"SyntaxError: {e}")); continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                problems.append((p, "Bare except detected"))
            if isinstance(node, ast.ImportFrom) and node.names and any(n.name=="*" for n in node.names):
                problems.append((p, "Wildcard import detected"))
        if "def main(" not in src and "if __name__ == '__main__':" not in src:
            if "print(" in src and "tests" not in str(p):
                problems.append((p, "print() in library code"))
        if "requests" in src and REQ_NO_TIMEOUT.search(src):
            problems.append((p, "requests call without timeout"))
    if problems:
        msg = "\n".join(f"- {path}: {why}" for path, why in problems[:50])
        raise RuntimeError(f"Guardrails failed:\n{msg}")
7) Snapshot output discipline
Trim giant diffs; force explicit --update-snapshots.

# src/ai_guardrails/_snap.py
import pytest

def pytest_addoption(parser):
    parser.addoption("--update-snapshots", action="store_true", default=False)

@pytest.fixture
def snapshot(request):
    update = request.config.getoption("--update-snapshots")
    def _assert(name: str, value: str):
        p = request.path.parent / f"__snapshots__/{request.node.name}__{name}.txt"
        if update:
            p.parent.mkdir(exist_ok=True); p.write_text(value)
            return
        expected = p.read_text() if p.exists() else None
        assert expected is not None, f"Missing snapshot {p}. Run with --update-snapshots."
        assert value == expected[:20000], "Snapshot mismatch (trimmed to 20k chars)."
    return _assert
pytest plugin entrypoint
# src/ai_guardrails/plugin.py
from ._net import pytest_runtest_setup as _net_setup
from ._time import deterministic_env as _det_env, freeze_now as _freeze_now
from ._fs import guard_writes as _guard_writes
from ._perf import ban_sleep as _ban_sleep, pytest_addoption as _perf_opts, pytest_runtest_call as _timeout_call
from ._secrets import pytest_sessionstart as _secrets_scan
from ._style import pytest_collection_finish as _style_scan
from ._snap import snapshot as _snapshot, pytest_addoption as _snap_opts

# pytest discovers fixtures/hookimpls via names; importing binds them.
__all__ = [
    "_net_setup", "_det_env", "_freeze_now", "_guard_writes",
    "_ban_sleep", "_timeout_call", "_secrets_scan", "_style_scan", "_snapshot",
    "_perf_opts", "_snap_opts",
]
pyproject.toml (uv-friendly)
[project]
name = "ai-guardrails"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["pytest>=8", "freezegun>=1.4"]

[project.entry-points.pytest11]
ai_guardrails = "ai_guardrails.plugin"
Install locally with uv:

uv pip install -e .
pytest -q  # guardrails activate automatically
Useful markers (document in README)
@pytest.mark.net — allow network

@pytest.mark.fs — allow writing outside tmp

@pytest.mark.timing — allow sleeps or timing-sensitive code

@pytest.mark.slow — exempt from default timeout (or extend with --max-test-seconds=30)

Add this to pytest.ini:

[pytest]
markers =
  net: allows network I/O
  fs: allows writes outside tmp
  timing: allows sleep/time-sensitive behavior
  slow: long-running test
Pre-commit companion (fast feedback before pytest)
Add lightweight checks mirroring the plugin:

ruff rules: ban bare except, wildcard imports

detect-secrets pre-commit hook

regex for requests.*( without timeout=

forbid print( in src/ (allow in tests/)

.pre-commit-config.yaml snippet:

repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks: [{ id: ruff, args: [--fix] }]
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks: [{ id: detect-secrets, args: [--baseline=.secrets.baseline] }]
  - repo: local
    hooks:
      - id: no-requests-without-timeout
        name: no requests without timeout
        entry: bash -c "grep -R \"requests\\.(get\\|post\\|put\\|delete)(\" -n src | grep -v timeout || true"
        language: system
        pass_filenames: false
        exclude: tests/
      - id: no-print-in-src
        name: no print in src
        entry: bash -c "grep -R \"print(\" -n src && exit 1 || true"
        language: system
        pass_filenames: false
Minimal adoption checklist
 uv pip install -e . in your repo

 Add pytest.ini markers

 Add pre-commit hooks & run pre-commit install

 Flip tests that truly need network/filesystem to use markers

 Set --max-test-seconds=5 (tune in CI)

 Add snapshot fixture where output stability matters

 Run once, fix violations, bask in the newfound sanity

Next expansions (when you want to get spicy)
Flake test detector: automatic rerun N times; fail on variance

Hypothesis profile: default strategies with time budget + falsifying examples saved

Subprocess guard: patch subprocess.run to require check=True, timeout=

Log budget: cap log volume per test (encourage structured logs)

Mutation smoke: run a tiny mutmut/eradicate subset nightly to catch vacuous tests

Import time budget: fail if a top-level import exceeds X ms (agents often add heavy imports)

If you want, I can wrap this into a ready-to-publish repo skeleton (with CI, badges, and docs) or tailor the guards to your Redwing/Seedling ecosystems. What shall I prioritize first, boss?

You said:
I love these ideas. I have some others like AAA comments. It feels weird though to have tests fail or error in these kinds of things.
ChatGPT said:

Thought for 13s
Totally hear you, Jeff. If tests “fail” over style/guardrail stuff, devs tune it out. Let’s split the suite into advisory vs. enforcing modes and make most rules non-failing by default—you still get visibility, trends, and CI gates when you want them.

Here’s how I’d shape it.

Philosophy
Advisory by default: surface issues as diagnostics (sections, warnings, summary tables), not failures.

Per-rule severity: each check can be advice | warn | error. Only error affects exit codes in strict modes.

Three modes

advisory: never fails tests or the session; produces rich reports + GitHub annotations.

quality-gate: session fails only if a budget is exceeded (e.g., >10 warnings, or any error).

strict: rules marked error fail immediately (good for nightly/CI).

UX knobs
In pyproject.toml:

[tool.ai_guardrails]
mode = "advisory"          # advisory | quality-gate | strict
budget.warn = 25           # only used in quality-gate
budget.error = 0
suppress = ["print-in-src"]  # rule ids to silence globally
elevate = { "secrets" = "error", "net-no-timeout" = "error" }  # per-rule overrides

[tool.ai_guardrails.rules]
aaa-comments = { severity = "advice" }
net-default-off = { severity = "warn" }
fs-sandbox = { severity = "warn" }
sleep-banned = { severity = "warn" }
secrets = { severity = "error" }
requests-timeout = { severity = "warn" }
print-in-src = { severity = "advice" }
CLI overrides (nice for CI):

pytest --guardrails-mode=strict --guardrails-budget-warn=0 --guardrails-budget-error=0
Reporting without failing
Per-test sections: attach diagnostics to the report so they show right under the test in -vv.

Terminal summary table: one glance at counts by rule.

JUnit properties: pipe into CI (GitHub Actions test summary).

SARIF (optional): feed annotations directly to PRs.

Core scaffolding
# src/ai_guardrails/_core.py
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Finding:
    rule_id: str
    severity: str   # advice|warn|error
    path: str
    location: tuple[int,int] | None
    message: str
    test_nodeid: str | None = None

class GuardrailsState:
    def __init__(self, config):
        self.mode = config.getoption("--guardrails-mode") or "advisory"
        self.budget_warn = float(config.getoption("--guardrails-budget-warn") or "inf")
        self.budget_error = float(config.getoption("--guardrails-budget-error") or "inf")
        self.findings: list[Finding] = []
        self._per_test: dict[str, list[Finding]] = defaultdict(list)

    def add(self, finding: Finding):
        self.findings.append(finding)
        if finding.test_nodeid:
            self._per_test[finding.test_nodeid].append(finding)

def pytest_addoption(parser):
    g = parser.getgroup("ai-guardrails")
    g.addoption("--guardrails-mode", action="store", default=None,
                help="advisory|quality-gate|strict")
    g.addoption("--guardrails-budget-warn", action="store", default=None)
    g.addoption("--guardrails-budget-error", action="store", default=None)

def pytest_configure(config):
    config._ai_guardrails = GuardrailsState(config)

def add_section(item, title, lines):
    # Attach a non-failing section to the test output
    item.add_report_section("call", f"ai-guardrails: {title}", "\n".join(lines))

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    st = config._ai_guardrails
    by_rule = defaultdict(int)
    for f in st.findings: by_rule[(f.rule_id, f.severity)] += 1
    if not by_rule: return
    tw = terminalreporter._tw
    tw.write("\nai-guardrails summary:\n")
    for (rule, sev), n in sorted(by_rule.items()):
        tw.write(f"  - {rule:22} [{sev:6}] : {n}\n")

def pytest_sessionfinish(session, exitstatus):
    st = session.config._ai_guardrails
    if st.mode == "advisory":
        return
    warn = sum(1 for f in st.findings if f.severity == "warn")
    err  = sum(1 for f in st.findings if f.severity == "error")
    if st.mode == "quality-gate":
        if err > st.budget_error or warn > st.budget_warn:
            session.exitstatus = 1
    elif st.mode == "strict":
        if err > 0:
            session.exitstatus = 1
Example: AAA-comments rule (non-failing default)
Goal: Encourage Arrange–Act–Assert structure without breaking builds.

Heuristic: Within a test function, look for three ordered comment blocks (case-insensitive) labeled arrange, act, assert. Purely advisory.

# src/ai_guardrails/_aaa.py
import ast, tokenize, io, pathlib, pytest
from ._core import Finding

def _aaa_findings(path: pathlib.Path, src: str):
    # Map line->comment text
    comments = {}
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            comments[tok.start[0]] = tok.string.lower()

    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            start = node.lineno
            end = max([getattr(node, "end_lineno", start)] + [start])
            seq = []
            for ln in range(start, end + 1):
                c = comments.get(ln, "")
                if "arrange" in c: seq.append(("arrange", ln))
                elif "act" in c:   seq.append(("act", ln))
                elif "assert" in c:seq.append(("assert", ln))
            if not seq:
                yield Finding("aaa-comments", "advice", str(path), (start, 0),
                              f"{node.name}: consider adding AAA comments (arrange/act/assert).")
            else:
                labels = [k for k,_ in seq]
                # Must contain in order: arrange -> act -> assert
                want = ["arrange","act","assert"]
                pos = [next((i for i,l in enumerate(labels) if l==w), None) for w in want]
                if any(p is None for p in pos) or not(pos[0] < pos[1] < pos[2]):
                    ln = seq[0][1]
                    yield Finding("aaa-comments", "advice", str(path), (ln, 0),
                                  f"{node.name}: AAA comment order missing/incorrect; found {labels}.")

def pytest_collection_finish(session):
    cfg = session.config
    root = cfg.rootpath
    for p in pathlib.Path(root).rglob("test_*.py"):
        try: src = p.read_text(encoding="utf-8")
        except Exception: continue
        for f in _aaa_findings(p, src):
            cfg._ai_guardrails.add(f)
This never fails tests; it just shows up in the Guardrails summary and (optionally) as a per-test section if you attach it during item setup. If you ever want to enforce AAA for a particular repo, bump severity in config.

Example: “don’t fail, just surface” per-test diagnostics
# Anywhere inside a hook where you have `item`
from ._core import add_section
def pytest_runtest_setup(item):
    # Imagine we saw a ban-sleep violation while scanning the file…
    findings = getattr(item.config, "_ai_guardrails")._per_test.get(item.nodeid, [])
    if findings:
        lines = [f"- {f.rule_id} [{f.severity}] {f.message} ({f.path}{':' + str(f.location[0]) if f.location else ''})"
                 for f in findings]
        add_section(item, "advisories", lines)
Where to put “hard” enforcement
Secrets, private keys, hard-coded tokens: keep as error (even in advisory, you still want red flags).

Live network in unit tests: default warn; devs can opt-in with @pytest.mark.net.

AAA, prints, wildcard imports, snapshots: default advice.

CI strategy that feels good
Local/dev: mode=advisory → never blocks flow; gives hints + pretty table.

PR CI (fast): mode=quality-gate, budget.warn=10, budget.error=0 → catches egregious stuff.

Nightly/full: mode=strict for a subset of rules (e.g., secrets + timeouts).

Nice extras (still non-disruptive)
Trend artifact: write ai_guardrails_report.json with per-rule counts; a tiny GH Action can plot deltas.

GitHub annotations: emit ::warning file=...,line=...:: message for warn/error so hints show inline.

Rule opt-outs: # guardrails: ignore=<rule-id> comment, tracked in the report so exceptions are visible.

If you want, I’ll wire this into your earlier skeleton (keeping your markers), and flip the default to advisory so nothing fails unless you opt into stricter modes. Want me to add the AAA rule plus the reporting/summary plumbing next, or prioritize the quality-gate budgets?

You said:
Ah that makes sense to set some as warnings by default or advisories. What is the serif thing you mentioned
ChatGPT said:
Ah — I think you caught me, Jeff. I didn’t mean “serif” (like a font). I was talking about SARIF.

👉 SARIF = Static Analysis Results Interchange Format.
It’s a standardized JSON schema for reporting diagnostics (errors, warnings, advisories) from tools like linters, security scanners, or in our case, pytest guardrails.

Why it’s cool in this context:

GitHub and Azure DevOps both understand SARIF natively.

If your plugin emits a results.sarif file, CI can upload it and GitHub will show inline annotations directly in PRs (red/yellow squiggles at the offending lines).

It lets you separate “test failures” from “quality findings.” Tests can all be green while the SARIF annotations still nudge contributors to clean things up.

So the flow could be:

Guardrails runs in advisory mode.

Instead of failing tests, it collects findings (AAA comments missing, bare excepts, no timeouts, etc.).

Writes them out to .ai_guardrails/report.sarif.

Your GitHub Action uses upload-sarif to make them show up in the PR.

That way AAA-comments or print statements don’t feel punitive, but developers still see them in their review surface.

Would you like me to sketch out a minimal SARIF emitter for your plugin so it drops a compliant JSON file each pytest run?

You said:
Love it.

I have issues with ai coders going crazy with tests. Writing tests that are basically the same thing. Also not making good test fixtures and repeat the same ones over and over. What kind of algorithm can catch that kind of thing
ChatGPT said:

Thought for 7s
Got you, Jeff. If the problem is “AI coders spawn 15 near-identical tests with copy-pasta setup,” we can nail it from two angles: static clone detection (what the test looks like) and dynamic behavioral similarity (what the test does). Mixing both keeps false positives low.

The algorithms I’d use
1) Static near-duplicate clustering (AST-based “code clone” finder)
Goal: Catch Type-1/2/3 clones (identical, renamed, lightly edited tests).

How:

Parse each test_* function into AST.

Normalize aggressively:

Strip comments/whitespace.

Replace identifiers with role tokens (e.g., var_1, func_2), normalize literals (e.g., all ints → INT, strings → STRLEN_#).

Canonicalize arrange/act/assert blocks if you have AAA tags.

Generate a structural fingerprint:

Option A: hash(normalized_ast.dumps()) (Merkle-like).

Option B: n-gram over AST node types + SimHash.

Option C: MinHash of token shingles (5-grams) + LSH buckets.

Cluster by fingerprint distance (Hamming for SimHash, Jaccard for MinHash).

Flag clusters with:

≥ 3 tests and pairwise distance < threshold (e.g., Hamming ≤ 6 bits on 128-bit SimHash).

Or 2 tests that are ≥ 90% similar and assert structure is isomorphic.

Why it works: Even if names differ or literals change a bit, structure stays the same.

Bonus: Compute a “fixture opportunity score” = average length of repeated setup slices across the cluster. If many lines prior to first assertion match, suggest extracting a fixture or a factory helper.

2) Dynamic behavior clustering (coverage signatures)
Goal: Catch tests that execute the same code paths and assert the same things, despite textual differences.

How:

Run with coverage (via coverage.py) and collect executed (file, line) sets per test (pytest --cov-context=test is perfect).

For each test, build a coverage signature (bitset or sorted tuple).

Compute Jaccard similarity between signatures.

Cluster pairs with Jaccard ≥ 0.95 (tuneable).

Within clusters, also compare assert shapes:

Extract count/types of assert calls from AST (assert, pytest.raises, np.testing.*, etc.).

Consider artifact outputs (same snapshot names, same exceptions).

Flag a cluster as redundant if:

Coverage Jaccard ≥ 0.95, and

Assert-shape vector distance ≤ small epsilon (same pattern), and

Param values differ trivially (e.g., different strings that never change code path).

Why it works: Text can differ, but if behavior is equivalent, it’s likely redundant.

3) Parametrization suggester (merge “same test, many inputs”)
Goal: Recommend replacing repeated tests with @pytest.mark.parametrize.

How:

For clusters from (1) or (2), align literals/kwargs in the call tree (AST walk of the “Act” section).

If the only diffs are a small set of input constants (strings/ints/enums), propose:

@pytest.mark.parametrize("name,limit,flag", [
    ("Alice", 10, True),
    ("Bob",   10, True),
    ("Eve",   12, False),
])
def test_foo(name, limit, flag, my_fixture): ...
Emit a machine-generated table of suggested parameters and a prototype refactor.

Heuristic: If ≥ 3 tests differ in ≤ k literals (k≤3), strong candidate for parametrization.

4) Fixture extraction detector (repeated Arrange blocks)
Goal: Detect copy-pasted setup ripe for a fixture/factory.

How:

Inside each test, split into Arrange/Act/Assert regions (AAA comments or heuristics: first assert boundary).

Hash the Arrange region to a normalized AST fingerprint (rename-agnostic).

Find Arrange-fingerprint clusters across the suite.

For clusters with ≥ 2 members and ≥ N lines, propose a fixture or factory function:

Fixture if the setup has I/O or heavyweight objects.

Factory if setup is pure object construction.

Emit a suggested fixture name (e.g., user_with_orders) from noun-phrases in variable names/types.

5) Anti-pattern classifiers (fast AST rules)
Assertion smell: multiple tests asserting the exact same constant or same exception type with identical message → likely redundant.

Param fakery: many tests, each with one literal changed but not used in code path (detected via coverage: literal’s site not executed).

Mock-bloat: tests differ only in mock names but patch the same targets with identical specs/returns.

Implement as small AST/coverage-aware rules that add advisory findings.

How this fits your pytest plugin
Data we collect per test
nodeid

Normalized AST features:

AST node type n-grams

Assert shape vector (counts by assert kind)

Literal map (names → placeholders)

Arrange block fingerprint (if AAA or heuristic split)

Coverage signature (line set)

Fixture usage (from item.fixturenames)

Scoring + thresholds
Near-duplicate (static): SimHash Hamming ≤ 6/128

Near-duplicate (dynamic): Coverage Jaccard ≥ 0.95

Parametrization candidate: ≥ 3 tests, literals differ in ≤ 3 positions, coverage Jaccard ≥ 0.9

Fixture extraction: Arrange cluster size ≥ 2 and ≥ 6 lines or ≥ 5 AST statements

These are defaults; expose in pyproject.toml.

Output (advisory by default)
Cluster report with code frames:

Representative test

Members with diffs highlighted

Suggested @pytest.mark.parametrize block or fixture skeleton

Guardrails summary counts:

near-duplicate-static

near-duplicate-dynamic

param-suggestion

fixture-extraction

SARIF with locations on the first differing literal/assert.

Minimal code skeletons
SimHash over AST node n-grams
def ast_node_ngrams(tree, n=4):
    seq = []
    for node in ast.walk(tree):
        seq.append(type(node).__name__)
    return ["|".join(seq[i:i+n]) for i in range(len(seq)-n+1)]

def simhash(features):
    from hashlib import md5
    bits = [0]*128
    for f in features:
        h = int(md5(f.encode()).hexdigest(), 16)
        for i in range(128):
            bits[i] += 1 if (h >> i) & 1 else -1
    v = 0
    for i, w in enumerate(bits):
        if w > 0: v |= (1 << i)
    return v

def hamming(a,b): return (a^b).bit_count()
Coverage signature per test (pytest hook)
def pytest_runtest_logreport(report):
    if report.when != "call": return
    cov = getattr(report, "coverage", None)  # use coverage plugin API or read .coverage data
    sig = frozenset(cov.executed_lines_for(report.nodeid))  # pseudo
    state = report.config._ai_guardrails
    state.coverage[report.nodeid] = sig
(You’ll actually integrate via coverage.Coverage() APIs with dynamic_context="test_function" so executed lines are keyed per test.)

Param suggestion (diff literal vectors)
def literal_vector(tree):
    lits = []
    class V(ast.NodeVisitor):
        def visit_Constant(self, n):
            if isinstance(n.value, (int, float, str, bool)):
                lits.append(type(n.value).__name__)
    V().visit(tree)
    return tuple(lits)

# group tests where literal_vector matches except positions P
Fixture vs factory decision tree
Touches FS/Net/DB/time? → fixture (can bake in tmp paths, monkeypatch).

Pure object graph construction? → factory helper (make_user(...)).

Used across many modules? → fixture in conftest.py, else local helper.

We can auto-emit a proposed fixture like:

@pytest.fixture
def user_with_orders(order_count=3):
    user = UserFactory()
    for _ in range(order_count):
        user.add_order(OrderFactory())
    return user
Putting it together in your suite
Collect features during collection (pytest_collection_modifyitems) → static fingerprints, AAA regions.

Collect coverage during run with dynamic_context=test_function.

After session, perform clustering + heuristics → generate:

Terminal table (advisory)

report.sarif

Optional report.md with codeframes and suggested param/fixture snippets.

Quality-gate mode (optional): only fail if, say, ≥ N near-duplicates persist.

If you want, I’ll wire a first pass with:

AST SimHash + coverage Jaccard

Param/fixture suggestions

SARIF emitter

All advisory by default

Say the word and I’ll sketch the exact plugin files and a tiny demo repo you can drop into Seedling.

You said:
Would this be better as a pytest plugin or more of a standalone tool like mypy and ruff
ChatGPT said:
Great question, boss. Short answer: do both—but with a clean split.

Make a core analyzer library that does all the heavy lifting (AST clone-detection, AAA heuristics, fixture extraction suggestions, coverage signature clustering, SARIF emitter).

Ship two front-ends:

A pytest plugin for anything that benefits from per-test context (coverage, fixtures in use, markers, per-test advisories).

A standalone CLI (like ruff/mypy) for fast, repo-wide static checks and pre-commit.

Here’s why.

When a pytest plugin shines
Dynamic similarity: needs coverage.py with dynamic_context=test_function to build per-test line sets → only reliable inside pytest.

Fixture hygiene: easiest to see real fixture use (item.fixturenames) while tests run/collect.

Per-test UX: add non-blocking advisory sections under each test in -vv; great for dev ergonomics.

Selective scope: respect markers (@pytest.mark.net, @pytest.mark.slow) to tune advice.

When a standalone tool wins
Speed & frequency: blazing-fast static scans on every save or pre-commit, without booting pytest.

Editor/CI parity: behaves like ruff/mypy, easy to wire into pre-commit and “lint” CI jobs.

Repo-wide refactors: global clone detection & parametrization suggestions even outside tests (e.g., factories).

Fewer env hassles: no plugin import side-effects, no test collection flakiness.

Recommendation (hybrid architecture)
ai_guardrails/
  pyproject.toml
  src/ai_guardrails/core/            # shared engine
    __init__.py
    models.py        # Finding, Cluster, Rule, Severity
    tokenize_ast.py  # AST normalizer, n-grammer, SimHash/MinHash
    aaa.py           # AAA detectors
    clones.py        # static clone clustering
    fixtures.py      # arrange-fingerprint & fixture suggestions
    sarif.py         # SARIF writer
    report.py        # markdown/JSON emitter
  src/ai_guardrails/pytest_plugin/
    __init__.py
    plugin.py        # hooks: collect, runtest_logreport, terminal_summary
    coverage.py      # integration helpers
  src/ai_guardrails/cli/
    __init__.py
    main.py          # `ai-guardrails lint` + `--format sarif|json|md`
Config (one source of truth)
In pyproject.toml (used by both front-ends):

[tool.ai_guardrails]
mode = "advisory"  # advisory|quality-gate|strict
budget.warn = 25
budget.error = 0
enable = ["aaa-comments","static-clones","fixture-extract","requests-timeout","print-in-src"]
suppress = []
[tool.ai_guardrails.thresholds]
static_clone_hamming = 6
dynamic_cov_jaccard = 0.95
param_candidate_k = 3
Workflow you’ll love
Local dev (fast loop):
ai-guardrails lint . --format sarif --out .ai_guardrails/report.sarif
Pre-commit runs this (advisory only).

Run tests:
pytest -q → Plugin adds per-test advisories; no failures unless you opt into strict.

CI:

Job 1: ai-guardrails lint → upload SARIF to PR annotations.

Job 2: pytest --guardrails-mode=quality-gate → fails only if budgets exceeded.

What goes where
Check	Standalone CLI	Pytest plugin
AAA comment suggestions	✅	✅ (per-test section)
Static near-duplicate tests (AST/SimHash/MinHash)	✅	✅
Fixture extraction (repeated Arrange)	✅	✅ (uses real fixtures too)
Dynamic duplicate tests (coverage Jaccard)	🚫	✅ (requires test contexts)
“Parametrize these” suggestions	✅	✅
Requests without timeouts, print in src, bare except	✅	optional (advice)
SARIF emission	✅	✅
Per-test advisory sections	🚫	✅
Minimal interface sketch
CLI entrypoint

# src/ai_guardrails/cli/main.py
import argparse
from ai_guardrails.core import run_static_analysis, write_sarif

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--format", choices=["sarif","json","md"], default="sarif")
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    findings, clusters = run_static_analysis(args.paths)
    if args.format == "sarif":
        doc = write_sarif(findings, clusters)
        print(doc if args.out == "-" else open(args.out,"w").write(doc))
Pytest plugin hook

# src/ai_guardrails/pytest_plugin/plugin.py
import pytest
from ai_guardrails.core import (
    collect_static_features_for_tests,
    record_per_test_coverage,
    cluster_and_advise, write_sarif
)

def pytest_collection_modifyitems(session, config, items):
    collect_static_features_for_tests(items)

def pytest_runtest_logreport(report):
    if report.when == "call":
        record_per_test_coverage(report)  # uses coverage dynamic context

def pytest_sessionfinish(session, exitstatus):
    findings, clusters = cluster_and_advise(session.config)
    write_sarif(findings, clusters, path=".ai_guardrails/report.sarif")
Practical decision tree (if you had to pick one first)
Need dynamic duplicate detection based on executed lines? Start with pytest plugin.

Want fast adoption, pre-commit & PR annotations with zero pytest coupling? Start with standalone CLI.

You have capacity for both (recommended): Build core first, then thin adapters.

Performance notes
Static pass can be made ruff-fast: parse each file once, compute AST n-grams, SimHash, and cache .guardrails-cache/ keyed by file mtime.

Pytest dynamic pass adds little overhead if you reuse coverage data (no per-line introspection during hot path; crunch at session end).

CI snippets
Pre-commit

- repo: local
  hooks:
    - id: ai-guardrails
      name: ai-guardrails
      entry: ai-guardrails lint .
      language: system
      pass_filenames: false
GitHub Action (SARIF upload)

- name: Guardrails (static)
  run: ai-guardrails lint . --format sarif --out .ai_guardrails/report.sarif
- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v3
  with: { sarif_file: .ai_guardrails/report.sarif }
If you want, I’ll draft the core engine API and minimal CLI + pytest adapter so Lily can drop it into Seedling. We’ll start with static clones, AAA, and fixture suggestions in the CLI; then add the dynamic coverage clustering in the plugin. Sound good?

You said:
Iterate on the name for me
ChatGPT said:
Alright, let’s play with some names. Since this suite is meant to guard against silly AI-written tests, the name should signal:

Protection / guardrails

Code quality / testing

Sass and bite (because you’re swatting down nonsense)

Here are some directions:

Guard/Protector theme
TestSentinel – stands watch over your test suite.

PytestGuardian – clear that it’s a plugin.

Aegis – shield of Zeus, sleek single-word vibe.

TestWard – “ward” as in guarding against bad patterns.

Sanity / Cleanliness theme
TestHygiene – all about clean, maintainable tests.

PySanity – keeps your test suite sane.

TestLint – like flake8/ruff, but for test smells.

SpecClean – keeps your specs/specifications clean.

Anti-gremlin / Whimsy theme
GremlinSquash – direct nod to squashing silly AI gremlins.

TestGoblin – mischievous, fun branding.

PyBouncer – only lets in well-behaved tests.

TestPoltergeist – catches the ghosts of duplicate tests.

Professional polish theme
Assure – play on “assert” + “assurance.”

Verify – crisp, single word.

Obsidian – strong, sharp, protective.

Argus – mythic watchman with a hundred eyes.

If you imagine this more like mypy/ruff, I’d go with a sleek, one-word CLI-friendly name (easy to type, brandable):

Testlint

Sentinel

Assure

Argus

If you see it as primarily a pytest plugin, then PytestGuardian or TestHygiene makes the purpose super clear.

Do you want the branding to lean more toward:
👉 fun/whimsical (GremlinSquash),
👉 serious/professional (Assure, Sentinel),
or 👉 explicit functional clarity (PytestGuardian, TestLint)?

You said:
Needs to be fun. Maybe something hinting at keeping ai agents have n track
ChatGPT said:
Fun and AI-agent-wrangling, got it 🌸. Let me throw some playful names at you that hint at keeping rowdy coding bots on track:

Mischief-Control Vibe
TestTamer – you tame the wild AI test menagerie.

GremlinWrangler – wrangles silly little gremlins the AI spawns.

BotBouncer – keeps unruly bot-written tests out of the club.

TestShepherd – gently but firmly keeps the flock in line.

Fun + Guardrails
RailBuddy – friendly, but keeps code on the rails.

TrackDog – playful watchdog, keeps AI on track.

CodeConductor – like a train conductor keeping everything on track.

Bugzapper – silly tests get zapped.

AI-aware Twists
RoboWrangler – cowboy energy, but for AI-written tests.

AgentTether – keeps your AI agents from running off.

TestNanny – “don’t do that, sweetie.”

AICorrall – all the AI horses penned where they belong.

Short, Punchy, CLI-friendly
Gremlin – just one word, but clear branding: “run gremlin lint.”

Tamer – simple, implies control.

Wrangle – fun to type, unique in the ecosystem.

Corrall – metaphor of gathering scattered AI tests.

If you imagine developers typing it all the time (like ruff, mypy), I’d lean toward Gremlin or Wrangle: one word, fun, memorable, easy to brand.

If you want it to read as explicitly about tests, then TestTamer or BotBouncer balances playful + clear purpose.

Do you want this to feel more like a mascot/tool with a personality (e.g., Gremlin, TestNanny) or like a professional but cheeky linter name (e.g., Wrangle, Tamer)?

You said:
My current on is pytest-drill-sergeant
ChatGPT said:
Ohhh I like pytest-drill-sergeant — it’s got that playful, “shaping up sloppy recruits” energy. If you want to explore in that same lane (fun, bossy, wrangling AI agents), here are some riffs:

Military / Training Camp Flavor
pytest-bootcamp – puts tests through discipline training.

pytest-sarge – short, snappy, keeps the drill-sergeant vibe.

pytest-taskmaster – bossy but fun.

pytest-barracks – keeps all your tests in order.

pytest-cadet-check – makes sure your baby AI cadet tests are up to code.

Wrangling Bots Flavor
pytest-bot-wrangler – you round up the AI’s test chaos.

pytest-test-nanny – cheeky, “don’t do that, sweetie.”

pytest-agent-herder – herding those wild AI-generated agents.

pytest-bot-bouncer – only lets the right tests past the velvet rope.

pytest-corrall – pens in AI’s runaway horses.

Fun + Snark
pytest-whip – cracks down on sloppy tests.

pytest-smackdown – lays the smack on nonsense.

pytest-sanity-check – keeps the suite sane.

pytest-clone-patrol – stops those copy-pasta duplicates.

pytest-bugzapper – zaps the silly stuff instantly.

If you like the drill-sergeant personality, I’d keep it in that tough love / bootcamp zone — because it gives the tool a voice. If you want more of a bot wrangler vibe, then bot-wrangler or agent-herder nails the AI angle while staying fun.

👉 Do you want the name to lean more into the military-commander persona (like drill-sergeant), or the cowboy/bouncer herding AI bots persona?

You said:
I’m leaning in the military side but I like gremlin too. The readme for sergeant is super fun and snarky
ChatGPT said:
Got it — if you’re vibing with military drill-sergeant energy and the cheeky “gremlin-squashing” angle, we can blend those into a little naming family. Think of it as building the character of the tool in the same way your README voice does.

Military + Mischief Hybrids
pytest-gremlin-squad – your squad that hunts down AI test gremlins.

pytest-gremlin-buster – Ghostbusters meets bootcamp.

pytest-gremlin-drill – every gremlin through the training drill.

pytest-gremlin-corps – elite corps against silly test clones.

pytest-gremlin-patrol – always on watch, never off duty.

Pure Military Attitude
pytest-drill-sergeant (your current one, strong baseline 💪)

pytest-gunnery-sarge – even harsher.

pytest-commissar – brutal enforcer.

pytest-brigadier – high rank, still snarky.

pytest-bootcamp – every test has to earn its stripes.

Gremlin as the Mascot
If you want gremlin to be the star while keeping the army drill vibe:

pytest-gremlin-sergeant

pytest-sergeant-gremlin

pytest-gremlin-drill-sergeant (long, but hilarious)

pytest-gremlin-ops (special operations, gremlin edition)

pytest-gremlin-guard

⚙️ Positioning Tip:

If you want this to feel like a fun linter, short & punchy is best (pytest-gremlin, pytest-sarge).

If you want it to feel like a character/tool with a voice, longer is funnier (pytest-gremlin-drill-sergeant, pytest-bugzapper-corps).

Would you like me to draft you a fun/snarky README intro paragraph for pytest-drill-sergeant that leans into this military-gremlin tone? I can give it that “you’re in bootcamp now, maggot” flavor that will make people smile when they read it.

You said:
Read this https://pypi.org/project/pytest-drill-sergeant/
ChatGPT said:
Cool, I read the PyPI page for pytest-drill-sergeant. Iris here with what stood out, what’s strong, and a few suggestions now that we’ve seen the “real thing.”

What hits really well
Voice & tone: That snarky military style is dead-on. “LISTEN UP, MAGGOTS!”, “Your test suite is a DISASTER!”, etc. It sets expectations immediately and is fun to read.

Clarity of features: AAA enforcement, marker enforcement, auto marker detection, synonyms for AAA, configuration options, good examples of before/after. Folks get what it does quickly.

Configurations: The “Baby steps” vs “NO MERCY” options let users ease in. That’s smart — lowers friction.

Synonyms support: Recognizing that teams may have different stylistic preferences. (Even though the Sergeant complains about it — great humor.)

What could be refined or expanded
Flexibility vs strictness: Right now, per the page, one violation = test fails (“Zero Tolerance Policy - One violation = one failed test. NO EXCEPTIONS!”). You may want to offer modes where some rules are warning/advisory only.

Duplication detection & fixture suggestions: Things like “stop repeating arrange blocks” or “duplicate tests” isn’t explicitly in the features. Based on your earlier ideas, adding this would broaden what Drill Sergeant can enforce.

Coverage-based behavior: Not mentioned. Might be good to distinguish static structure vs what the test actually exercises.

SARIF / PR annotation: Not visible from PyPI page. Having that as part of the offering would help adoption (CI visibility, inline feedback).

Performance & error message noise: Strict tooling can cause many failures initially; you have “Baby steps” settings, but might also need some “quiet mode” or summarization.

Suggestions in alignment with what you want
Given your ideas (detect duplicate tests, suggest fixtures, etc.), here are tweaks or additions that line up with the existing Drill Sergeant identity:

Add “duplicate test detection / redundancy badge”
E.g., “Clone patrol: telling you when you’re writing the same test twice so you can merge via parametrize.”

Make some rules advisory by default
Eg: AAA synonyms, fixture suggestion, duplicate detection → advisory mode (warnings) unless you opt into “strict bootcamp” mode.

Reporting / trend tracking
Maybe a “battlefield readiness score” — shows % of tests that passed quality metrics, duplicate test count, average description length, etc.

SARIF export so results show in PRs nicely.

If you want, I can propose a revised README intro (same voice) that incorporates your duplicate test detection & fixture suggestions, plus modes for warnings vs errors. Want me to write that up for you?

You said:
Tell me more about

3.	Reporting / trend tracking
Maybe a “battlefield readiness score” — shows % of tests that passed quality metrics, duplicate test count, average description length, etc.
ChatGPT said:
Absolutely, Jeff — Iris reporting for duty. Let’s turn pytest-drill-sergeant into a tiny quality intelligence system with a cheeky Battlefield Readiness Score™ and real trends over time.

What we’ll track (per run)
Think of each test run as producing a compact telemetry blob:

AAA compliance % — tests with valid Arrange/Act/Assert order.

Duplicate test clusters — static (AST-similarity) and dynamic (coverage Jaccard).

Parametrization ratio — % of tests covered by @pytest.mark.parametrize.

Fixture reuse score — repeated Arrange blocks that should be fixtures vs actual fixture usage.

Timeout hygiene — % of requests with explicit timeouts in touched code.

Forbidden patterns — bare except, wildcard imports, print in src, etc.

Nondeterminism traps — random, time.sleep, real network/filesystem hits without markers.

Slow test budget — % of tests exceeding a threshold; top offenders list.

Flake sniff (optional): re-run sample N times; variance >0 flags as flaky.

Battlefield Readiness Score (BRS)
A single 0–100 score so you can fail PRs softly or brag in the README.

Formula (default weights; tweak in config):

BRS = 100
  - 30 * (1 - AAA_rate)
  - 20 * duplicate_penalty
  - 10 * (1 - param_rate)
  - 10 * (1 - fixture_reuse_rate)
  - 10 * non_determinism_rate
  - 10 * slow_tests_rate
  - 10 * style_smell_rate
Where:

duplicate_penalty = min(1, (total_near_duplicate_tests / total_tests))

*_rate terms are proportions in [0,1].

Clamp to [0,100]. Provide per-component breakdown in the report.

Artifacts & formats
.ai_guardrails/report.json — detailed metrics + findings.

.ai_guardrails/report.sarif — inline PR annotations.

.ai_guardrails/summary.md — pretty Markdown for CI summary.

.ai_guardrails/history.jsonl — one line per run for trends.

JSON schema (lean)
{
  "run_id": "2025-09-12T14:30:01Z",
  "commit": "abc1234",
  "branch": "main",
  "total_tests": 412,
  "metrics": {
    "aaa_rate": 0.82,
    "duplicate_tests": 37,
    "duplicate_clusters": 9,
    "param_rate": 0.48,
    "fixture_reuse_rate": 0.61,
    "non_determinism_rate": 0.07,
    "slow_tests_rate": 0.11,
    "style_smell_rate": 0.05
  },
  "score": {
    "brs": 71.4,
    "components": {
      "aaa": 85.4, "duplicates": 62.0, "param": 76.0,
      "fixtures": 84.0, "nondet": 93.0, "slow": 89.0, "style": 95.0
    }
  },
  "top_offenders": {
    "slow_tests": ["tests/integration/test_sync.py::test_big_sync"],
    "duplicate_clusters": [
      {"repr": "tests/unit/test_user.py::test_valid_name",
       "members": 5, "suggestion": "parametrize(name)"}
    ]
  }
}
Trend tracking
Append each run to history.jsonl. That lets us plot BRS over time, track AAA gains, and surface regressions.

Minimal writer (inside plugin’s pytest_sessionfinish)
from pathlib import Path
import json, datetime, subprocess

def _git_rev():
    try:
        return subprocess.check_output(["git","rev-parse","--short","HEAD"]).decode().strip()
    except Exception:
        return None

def write_history_entry(report_dict):
    root = Path(".ai_guardrails"); root.mkdir(exist_ok=True)
    hist = root / "history.jsonl"
    with hist.open("a", encoding="utf-8") as f:
        f.write(json.dumps(report_dict, ensure_ascii=False) + "\n")
CI wiring (GitHub Actions)
Upload SARIF for PR annotations

Post a CI summary with the Markdown

Optionally commit history.jsonl to a metrics branch (keeps main clean)

name: guardrails
on: [push, pull_request]
jobs:
  guardrails:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/uv-action@v3
      - run: uv pip install . coverage pytest
      - run: |
          pytest -q --guardrails-mode=advisory
          echo "### Drill Sergeant Report" >> $GITHUB_STEP_SUMMARY
          cat .ai_guardrails/summary.md >> $GITHUB_STEP_SUMMARY
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: .ai_guardrails/report.sarif
      - name: Persist history (metrics branch)
        if: github.ref == 'refs/heads/main'
        run: |
          git fetch origin metrics:metrics || true
          git checkout -B metrics
          git add .ai_guardrails/history.jsonl
          git commit -m "metrics: append guardrails run" || echo "no changes"
          git push origin metrics
README badges (instant gratification)
Publish a static shields.io badge in CI based on the latest BRS:

![BRS](https://img.shields.io/badge/Battlefield%20Readiness-71.4-green)
Automate by writing a tiny SVG (or use shields’ “dynamic JSON” if you host the JSON somewhere). For repos with Pages enabled, drop latest.json on gh-pages and point shields at it.

Pretty report for humans
Generate .ai_guardrails/summary.md so CI can paste it:

## 🪖 Battlefield Readiness: **71.4 / 100**
- AAA compliance: **82%**
- Duplicate clusters: **9** (37 tests) → suggest **3** parametrizations, **2** fixtures
- Parametrization rate: **48%**
- Fixture reuse: **61%**
- Nondeterminism incidents: **7%**
- Slow tests: **11%** (threshold: 5s)
- Style smells: **5%**

### Top suggestions
- Parametrize `test_name_validity` (5 cases differ only by `name`)
- Extract fixture `user_with_orders` (repeated Arrange across 4 tests)
- Add `timeout=` to 3 `requests.get` calls in `client.py`
Quality gates (gentle)
Let folks start in advisory but keep a bar:

Fail PR if BRS drops by >5 vs base branch

Fail PR if duplicate_tests increases by >10

Fail PR if AAA_rate decreases by >3%

Implement by comparing current run to previous from metrics branch.

Config knobs (pyproject)
[tool.pytest_drill_sergeant.metrics]
enable = ["aaa","duplicates","parametrize","fixtures","nondeterminism","slow","style"]
thresholds.slow_seconds = 5.0
weights = { aaa=0.30, duplicates=0.20, parametrize=0.10, fixtures=0.10, nondeterminism=0.10, slow=0.10, style=0.10 }
gates = { max_brs_drop = 5, max_duplicate_increase = 10, min_aaa_rate = 0.75 }
How we compute the key pieces (quick specifics)
AAA_rate: good_AAA_tests / total_tests. “Good” = detected sections in order; synonyms allowed.

Duplicate_tests: union size of all clusters where

Static: SimHash Hamming ≤ threshold (e.g., 6/128) on AST n-grams of test bodies.

Dynamic (if coverage on): Jaccard(covered_lines(test_i), covered_lines(test_j)) ≥ 0.95 and assert shapes ~equal.

Param_rate: tests inside a parametrized node / total tests.

Fixture_reuse_rate: 1 − (repeated Arrange blocks length / total Arrange length). (We also emit concrete fixture suggestions.)

Nondeterminism_rate: tests that used forbidden things (sleep, real net/fs unmarked, random without seed) / total tests.

Slow_tests_rate: tests exceeding threshold / total tests.

Style_smell_rate: files with at least one smell / total files scanned.

Tiny Python for BRS calc (drop-in)
def brs(m):
    # m = metrics dict
    dup_pen = min(1.0, m["duplicate_tests"] / max(1, m["total_tests"]))
    score = 100
    score -= 30 * (1 - m["aaa_rate"])
    score -= 20 * dup_pen
    score -= 10 * (1 - m["param_rate"])
    score -= 10 * (1 - m["fixture_reuse_rate"])
    score -= 10 * m["non_determinism_rate"]
    score -= 10 * m["slow_tests_rate"]
    score -= 10 * m["style_smell_rate"]
    return max(0, min(100, round(score, 1)))
Why this works for culture
Devs see the issues (PR annotations), feel progress (trends), and aren’t blocked by advisory mode.

You still get gates when quality dips, not for one-off nits.

The snarky Sergeant voice remains the headline, but behind it is a clean, reproducible metrics engine.

If you want, I can draft the summary.md renderer and the history.jsonl writer as a PR-ready module, plus the GitHub Action to post the BRS badge.
