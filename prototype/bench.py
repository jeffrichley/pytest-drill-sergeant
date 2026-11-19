"""Throwaway prototype: how much time does static analysis add, and is caching worth it?

Usage: python -I bench.py <name> <test-root> [<test-root> ...]
"""

import ast
import hashlib
import os
import pickle
import shutil
import statistics
import sys
import tempfile
import time
from collections import defaultdict

FLAKY_CALLS = {"sleep", "time", "now", "today", "random", "randint", "choice", "shuffle"}
MOCK_CTORS = {"Mock", "MagicMock", "AsyncMock"}


def norm(node):
    """Structure fingerprint: names and constants erased."""
    class N(ast.NodeTransformer):
        def visit_Name(self, n):
            return ast.copy_location(ast.Name(id="_", ctx=n.ctx), n)

        def visit_Constant(self, n):
            return ast.copy_location(ast.Constant(value=0), n)

        def visit_Attribute(self, n):
            self.generic_visit(n)
            return n

    import copy
    return hashlib.blake2b(ast.dump(N().visit(copy.deepcopy(node))).encode(), digest_size=8).digest()


def raw(node):
    return hashlib.blake2b(ast.dump(node).encode(), digest_size=8).digest()


def call_name(c):
    f = c.func
    return f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)


def analyse_file(path, src):
    """Per-file work: parse, run representative local checks, build summary."""
    tree = ast.parse(src, filename=path)
    findings = []
    tests = []  # (name, line, setup-window hashes, body hash)
    lines = src.count("\n") + 1
    if lines > 500:
        findings.append(("file-length", 1))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test"):
            continue
        asserts = 0
        for sub in ast.walk(node):
            if isinstance(sub, ast.Assert):
                asserts += 1
                t = sub.test
                if isinstance(t, ast.Constant) or (isinstance(t, ast.Compare) and len(t.comparators) == 1 and ast.dump(t.left) == ast.dump(t.comparators[0])):
                    findings.append(("tautological", sub.lineno))
                if isinstance(t, ast.Compare) and any(isinstance(o, ast.In) for o in t.ops) and isinstance(t.left, ast.Constant) and isinstance(t.left.value, str):
                    findings.append(("string-match", sub.lineno))
            elif isinstance(sub, ast.Call):
                n = call_name(sub)
                if n in FLAKY_CALLS:
                    findings.append(("flaky", sub.lineno))
                elif n in MOCK_CTORS and not any(k.arg in ("spec", "spec_set") for k in sub.keywords):
                    findings.append(("mock-no-spec", sub.lineno))
                elif n == "raises" and not any(k.arg == "match" for k in sub.keywords):
                    findings.append(("broad-raises", sub.lineno))
                elif n in ("skip", "xfail") and not sub.args and not sub.keywords:
                    findings.append(("skip-no-reason", sub.lineno))
                elif n and n.startswith("assert_called"):
                    asserts += 1
            elif isinstance(sub, (ast.If, ast.For, ast.While)) and sub is not node:
                findings.append(("conditional", sub.lineno))
        if asserts == 0:
            findings.append(("no-assertion", node.lineno))
        if (node.end_lineno or node.lineno) - node.lineno > 50:
            findings.append(("long-test", node.lineno))
        body = node.body
        setup = [s for s in body if not isinstance(s, ast.Assert)]
        hashes = [norm(s) for s in setup]
        windows = {b"".join(hashes[i:i + 3]) for i in range(max(0, len(hashes) - 2))}
        tests.append((node.name, node.lineno, windows, norm(node)))
    return findings, tests


def cross_file(summaries):
    """Suite-level work on summaries only: copy-pasted setup and near-duplicate tests."""
    win = defaultdict(set)
    bodies = defaultdict(list)
    for path, (_, tests) in summaries.items():
        for name, line, windows, body in tests:
            for w in windows:
                win[w].add((path, name))
            bodies[body].append((path, name))
    pasted = sum(1 for v in win.values() if len(v) >= 3)
    dupes = sum(1 for v in bodies.values() if len(v) >= 2)
    return pasted, dupes


def discover(roots):
    out = []
    for root in roots:
        for d, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if x not in (".venv", "__pycache__", ".git")]
            out += [os.path.join(d, f) for f in files if f.startswith("test_") and f.endswith(".py")]
    return sorted(out)


def run_nocache(paths):
    s = {}
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as fh:
            s[p] = analyse_file(p, fh.read())
    return s


def run_hashcache(paths, cache):
    s = {}
    for p in paths:
        with open(p, "rb") as fh:
            b = fh.read()
        k = hashlib.blake2b(b, digest_size=16).hexdigest()
        if k in cache:
            s[p] = cache[k]
        else:
            s[p] = cache[k] = analyse_file(p, b.decode("utf-8", "replace"))
    return s


def run_mtimecache(paths, cache):
    s = {}
    for p in paths:
        st = os.stat(p)
        k = (p, st.st_mtime_ns, st.st_size)
        if k in cache:
            s[p] = cache[k]
        else:
            with open(p, encoding="utf-8", errors="replace") as fh:
                s[p] = cache[k] = analyse_file(p, fh.read())
    return s


def timed(fn, reps=5):
    ts = []
    for _ in range(reps):
        t = time.perf_counter()
        r = fn()
        ts.append(time.perf_counter() - t)
    return statistics.median(ts) * 1000, r


def main():
    name, roots = sys.argv[1], sys.argv[2:]
    paths = discover(roots)
    nlines = sum(sum(1 for _ in open(p, encoding="utf-8", errors="replace")) for p in paths)
    tmp = tempfile.mkdtemp()
    cpath = os.path.join(tmp, "cache.pkl")

    def with_disk_cache(runner, mutate=None):
        # load cache from disk, run, save back: what a real run does each time
        def go():
            cache = {}
            if os.path.exists(cpath):
                with open(cpath, "rb") as fh:
                    cache = pickle.load(fh)
            if mutate:
                mutate(cache)
            s = runner(paths, cache)
            with open(cpath, "wb") as fh:
                pickle.dump(cache, fh)
            return s
        return go

    t_none, s = timed(lambda: run_nocache(paths))
    t_cross, (pasted, dupes) = timed(lambda: cross_file(s))
    nfind = sum(len(f) for f, _ in s.values())
    ntests = sum(len(t) for _, t in s.values())

    rows = [("no cache", t_none)]
    for label, runner in (("content-hash cache", run_hashcache), ("mtime cache", run_mtimecache)):
        if os.path.exists(cpath):
            os.remove(cpath)
        cold, _ = timed(with_disk_cache(runner), reps=1)
        warm, _ = timed(with_disk_cache(runner))

        def drop_one(cache):  # simulate one edited file: evict ~1 entry
            if cache:
                cache.pop(next(iter(cache)))
        one, _ = timed(with_disk_cache(runner, drop_one))
        rows.append((f"{label}: cold (first run)", cold))
        rows.append((f"{label}: warm, nothing changed", warm))
        rows.append((f"{label}: warm, one file changed", one))
    csize = os.path.getsize(cpath)
    shutil.rmtree(tmp)

    print(f"\n## {name}: {len(paths)} files, {nlines} lines, {ntests} tests, {nfind} local findings, "
          f"{pasted} pasted-setup groups, {dupes} near-duplicate groups")
    print(f"cache file size: {csize/1024:.0f} KiB")
    print(f"{'mode':42} {'per-file ms':>12} {'+cross-file ms':>15} {'total ms':>10}")
    for label, t in rows:
        print(f"{label:42} {t:12.1f} {t_cross:15.1f} {t + t_cross:10.1f}")


if __name__ == "__main__":
    main()
