"""Following a test's calls into the helpers it calls, for the assertions they make.

A real assertion (GLOSSARY.md) is made in the test itself, or in a function in the
test tree that the test calls, at any depth, whose body holds one. The test tree is
the run's test files, every `conftest.py`, and the modules in or below a directory
that holds one of the run's test files, never production code: a production
`assert` is an invariant, not a check the test makes.

A call is followed only as far as the files show it:

- a name: a `def` in the module or the function, a name bound to one (`check =
  partial(_check, ...)`), or an import, absolute or relative, into another module of
  the test tree, through any re-exports;
- `self.x()` or `cls.x()`, through the first parameter of a method: the test's class
  and its bases, in the same file or imported; a `def` in a class body, a class
  attribute, or `self.x = ...` / `cls.x = ...` in any of its methods;
- `super().x()`: the bases of the class the call is made in;
- `module.f()`, through an imported module.

`functools.partial`, `staticmethod` and `classmethod` are seen through. A helper
whose own body makes no assertion but calls one of its own parameters asserts when
the call passes, for that parameter, an `assert*` function or a function that
asserts. A method on a value some call returned is never followed: what it is would
take the call's return type.

An absolute import is looked for under each directory above the importing file,
nearest first, as pytest's rootdir-style `sys.path` finds it; the first file found
is the module, followed only when it is in the test tree.

Each function's answer is worked out once per run and kept with the modules it
relied on, so a test file's result can name every module it followed (`followed`)
for the cache to check.
"""

import ast
import os
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from pytest_drill_sergeant.cache import content_hash
from pytest_drill_sergeant.checks.ast_tools import (
    bound_names,
    imports_seen_by,
    instance_param,
    is_real_assertion,
    module_imports,
    qualified,
    walk_test,
)
from pytest_drill_sergeant.checks.base import FunctionNode, TestFunction
from pytest_drill_sergeant.paths import absolute

_PARTIAL = "functools.partial"
_METHOD_WRAPPERS = frozenset({"staticmethod", "classmethod"})
_CONFTEST = "conftest.py"
_INIT = "__init__.py"


@dataclass(frozen=True)
class _Import:
    """What an import binds a name to: a module, or a name in one.

    Attributes:
        level: How many packages up a relative import starts; 0 for an absolute one.
        module: The module, dotted; empty for `from . import x`.
        attr: The name imported from the module, or `None` for the module itself.
    """

    level: int
    module: str
    attr: str | None


@dataclass(eq=False)
class _Module:
    """One parsed module of the test tree, with what its top level binds.

    Attributes:
        key: Its absolute path, as `paths.absolute` writes it.
        names: Its imports as `module_imports` gives them, for `is_real_assertion`.
        bindings: Each name its top level binds, to the statement or import that
            binds it last: a `def`, a `class`, a value or an `_Import`.
    """

    key: str
    names: dict[str, str]
    bindings: dict[str, object]


@dataclass(frozen=True)
class _Class:
    node: ast.ClassDef
    module: _Module


@dataclass(frozen=True)
class _Function:
    """A function to follow into, with the classes its `self` and `super()` reach.

    Attributes:
        node: The function, or a lambda.
        module: The module it is defined in.
        cls: The class it is defined in, for `super()`; `None` at module level.
        self_cls: The class its `self` or `cls` stands for: the test's own class
            when reached through it, else the class it is defined in.
    """

    node: FunctionNode | ast.Lambda
    module: _Module
    cls: _Class | None = None
    self_cls: _Class | None = None


# An argument, with the scope its expression is read in.
_Arg = tuple[ast.expr, "_Scope"]


@dataclass(frozen=True)
class _Callee:
    """A function a call reaches, with the arguments a `partial` already gave it."""

    function: _Function
    args: tuple[_Arg, ...] = ()
    keywords: tuple[tuple[str, _Arg], ...] = ()


@dataclass(eq=False)
class _Scope:
    """What the names in one function's body stand for.

    Attributes:
        module: The module the function is in.
        names: The imported names it sees, for `is_real_assertion`.
        cls: The class it is defined in, for `super()`.
        self_cls: The class its `self` or `cls` stands for.
        instance: The parameter that is `self` or `cls`, or `None`.
        positional: Its positional parameters in order, the instance aside.
        params: Every parameter it takes.
        values: The names its body binds with a plain assignment, to the value.
        imports: The names its body binds by import.
        functions: The functions its body defines, by name.
    """

    module: _Module
    names: dict[str, str]
    cls: _Class | None
    self_cls: _Class | None
    instance: str | None
    positional: list[str]
    params: set[str]
    values: dict[str, ast.expr] = field(default_factory=dict)
    imports: dict[str, _Import] = field(default_factory=dict)
    functions: dict[str, FunctionNode] = field(default_factory=dict)


@dataclass(frozen=True)
class _Answer:
    """Whether a function asserts, and which of its parameters it calls."""

    asserts: bool
    calls_params: frozenset[str] = frozenset()


_NO = _Answer(asserts=False)
_YES = _Answer(asserts=True)
_UNREACHED = 1 << 30


def _import_bindings(
    statement: ast.Import | ast.ImportFrom,
) -> Iterator[tuple[str, _Import]]:
    if isinstance(statement, ast.Import):
        for alias in statement.names:
            if alias.asname:
                yield alias.asname, _Import(0, alias.name, None)
            else:
                top = alias.name.split(".")[0]
                yield top, _Import(0, top, None)
        return
    for alias in statement.names:
        if alias.name != "*":
            yield (
                alias.asname or alias.name,
                _Import(statement.level, statement.module or "", alias.name),
            )


def _top_level(body: list[ast.stmt]) -> Iterator[ast.stmt]:
    """A module's top-level statements, with those under a top-level `if` or `try`."""
    for statement in body:
        yield statement
        if isinstance(statement, ast.If | ast.Try):
            for part in (
                statement.body,
                statement.orelse,
                getattr(statement, "finalbody", []),
                *(h.body for h in getattr(statement, "handlers", [])),
            ):
                yield from _top_level(part)


def _bindings(tree: ast.Module) -> dict[str, object]:
    bindings: dict[str, object] = {}
    for statement in _top_level(tree.body):
        if isinstance(statement, ast.Import | ast.ImportFrom):
            bindings.update(_import_bindings(statement))
        elif isinstance(
            statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ):
            bindings[statement.name] = statement
        elif (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            bindings[statement.targets[0].id] = statement.value
        elif not isinstance(statement, ast.If | ast.Try):
            for name in bound_names(statement):
                bindings.pop(name, None)
    return bindings


def _is_static(node: FunctionNode | ast.Lambda) -> bool:
    return isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and any(
        isinstance(d, ast.Name) and d.id == "staticmethod" for d in node.decorator_list
    )


def _body(node: FunctionNode | ast.Lambda) -> Iterator[ast.AST]:
    """Every node of a function's body, at any depth."""
    if isinstance(node, ast.Lambda):
        yield from ast.walk(node.body)
        return
    for statement in node.body:
        yield from ast.walk(statement)


def _final_name(expr: ast.expr) -> str | None:
    if isinstance(expr, ast.Attribute):
        return expr.attr
    return expr.id if isinstance(expr, ast.Name) else None


class TestTree:
    """The modules a run's tests may follow calls into, and what each function asserts.

    Built once per run. It parses each module at most once, works out each
    function's answer at most once (`Assertions` asks), and hashes each module at
    most once (`digest`).
    """

    __test__ = False  # Not a pytest test class, despite the name.

    def __init__(
        self, test_files: Iterable[Path], production: Iterable[Path] = ()
    ) -> None:
        """A run's test tree.

        Args:
            test_files: The run's test files; their directories, and every
                directory below them, are in the tree.
            production: Production code: files, and directories whose every file
                is, kept out of the tree.
        """
        self._dirs = {os.path.dirname(absolute(p)) for p in test_files}
        self._production_files: set[str] = set()
        self._production_dirs: list[str] = []
        for path in production:
            key = absolute(path)
            if path.is_dir():
                self._production_dirs.append(key.rstrip(os.sep) + os.sep)
            else:
                self._production_files.add(key)
        self._modules: dict[str, _Module | None] = {}
        self._files: dict[str, bool] = {}
        self._digests: dict[str, str] = {}
        self._resolved: dict[
            tuple[str, str, int], tuple[_Module | None, tuple[str, ...]]
        ] = {}
        self._answers: dict[_Function, tuple[_Answer, frozenset[str]]] = {}
        self._open: dict[_Function, int] = {}
        self._reach = _UNREACHED
        self._deps: list[set[str]] = []

    # --- What is in the tree ------------------------------------------------------

    def contains(self, key: str) -> bool:
        """Whether a file, by absolute path, is in the test tree."""
        if key in self._production_files or any(
            key.startswith(d) for d in self._production_dirs
        ):
            return False
        if os.path.basename(key) == _CONFTEST:
            return True
        directory = os.path.dirname(key)
        while True:
            if directory in self._dirs:
                return True
            parent = os.path.dirname(directory)
            if parent == directory:
                return False
            directory = parent

    def _is_file(self, key: str) -> bool:
        known = self._files.get(key)
        if known is None:
            known = self._files[key] = os.path.isfile(key)
        return known

    def digest(self, key: str) -> str:
        """A module's content hash, or empty when it is missing or not in the tree.

        A cached result followed each module under its digest; any change means
        the result is stale.
        """
        known = self._digests.get(key)
        if known is None:
            known = ""
            if self._is_file(key) and self.contains(key):
                try:
                    known = content_hash(Path(key).read_bytes())
                except OSError:
                    known = ""
            self._digests[key] = known
        return known

    def _note(self, key: str) -> None:
        if self._deps:
            self._deps[-1].add(key)

    # --- Modules ------------------------------------------------------------------

    def module(self, key: str, tree: ast.Module | None = None) -> _Module | None:
        """A module of the tree, parsed once; `None` when it can't be read or parsed."""
        if key in self._modules:
            return self._modules[key]
        found: _Module | None = None
        try:
            parsed = tree if tree is not None else ast.parse(Path(key).read_bytes())
        except (OSError, SyntaxError, ValueError):
            parsed = None
        if parsed is not None:
            found = _Module(
                key=key, names=module_imports(parsed), bindings=_bindings(parsed)
            )
        self._modules[key] = found
        return found

    def _resolve(self, dotted: str, level: int, origin: _Module) -> _Module | None:
        """The module an import names, when it is a file of the test tree."""
        start = os.path.dirname(origin.key)
        memo_key = (start, dotted, level)
        if memo_key not in self._resolved:
            self._resolved[memo_key] = self._look_up(dotted, level, start)
        module, noted = self._resolved[memo_key]
        for key in noted:
            self._note(key)
        return module

    def _look_up(
        self, dotted: str, level: int, start: str
    ) -> tuple[_Module | None, tuple[str, ...]]:
        parts = [p for p in dotted.split(".") if p]
        if level:
            base = start
            for _ in range(level - 1):
                base = os.path.dirname(base)
            bases = [base]
        else:
            bases = [start]
            while (parent := os.path.dirname(bases[-1])) != bases[-1]:
                bases.append(parent)
        noted: list[str] = []
        for base in bases:
            stem = os.path.join(base, *parts)
            candidates = (
                [stem + ".py", os.path.join(stem, _INIT)]
                if parts
                else [os.path.join(stem, _INIT)]
            )
            for candidate in candidates:
                exists = self._is_file(candidate)
                inside = self.contains(candidate)
                if exists or inside:
                    noted.append(candidate)
                if exists:
                    return (self.module(candidate) if inside else None), tuple(noted)
        return None, tuple(noted)

    def _member(  # noqa: PLR0911  # One return per kind of binding.
        self, module: _Module, name: str, seen: frozenset[tuple[str, str]]
    ) -> object:
        """What a module's top-level name is: a `_Callee`, `_Class`, `_Module` or `None`."""
        if (module.key, name) in seen:
            return None
        seen = seen | {(module.key, name)}
        bound = module.bindings.get(name)
        if bound is None:
            if module.key.endswith(os.sep + _INIT):
                return self._resolve(name, 1, module)
            return None
        if isinstance(bound, _Import):
            return self._imported(module, bound, seen)
        if isinstance(bound, ast.FunctionDef | ast.AsyncFunctionDef):
            return _Callee(_Function(bound, module))
        if isinstance(bound, ast.ClassDef):
            return _Class(bound, module)
        if isinstance(bound, ast.expr):
            return self._target(bound, self._module_scope(module), seen)
        return None

    def _imported(
        self, module: _Module, imported: _Import, seen: frozenset[tuple[str, str]]
    ) -> object:
        source = self._resolve(imported.module, imported.level, module)
        if imported.attr is None:
            return source
        found = None if source is None else self._member(source, imported.attr, seen)
        if found is None:
            dotted = f"{imported.module}.{imported.attr}".strip(".")
            found = self._resolve(dotted, imported.level, module)
        return found

    # --- Scopes -------------------------------------------------------------------

    def _module_scope(self, module: _Module) -> _Scope:
        return _Scope(
            module=module,
            names=module.names,
            cls=None,
            self_cls=None,
            instance=None,
            positional=[],
            params=set(),
        )

    def _scope(
        self,
        node: FunctionNode | ast.Lambda,
        module: _Module,
        cls: _Class | None,
        self_cls: _Class | None,
        names: dict[str, str] | None = None,
    ) -> _Scope:
        args = node.args
        positional = [a.arg for a in args.posonlyargs + args.args]
        instance = None
        if (
            cls is not None
            and not isinstance(node, ast.Lambda)
            and not _is_static(node)
        ):
            instance = positional[0] if positional else None
            positional = positional[1:]
        starred = [a.arg for a in (args.vararg, args.kwarg) if a is not None]
        scope = _Scope(
            module=module,
            names=names
            if names is not None
            else (
                module.names
                if isinstance(node, ast.Lambda)
                else imports_seen_by(node, module.names)
            ),
            cls=cls,
            self_cls=self_cls if instance is not None else None,
            instance=instance,
            positional=positional,
            params={*positional, *(a.arg for a in args.kwonlyargs), *starred}
            | ({instance} if instance else set()),
        )
        for child in _body(node):
            if isinstance(child, ast.Import | ast.ImportFrom):
                scope.imports.update(_import_bindings(child))
            elif (
                isinstance(child, ast.Assign)
                and len(child.targets) == 1
                and isinstance(child.targets[0], ast.Name)
            ):
                scope.values[child.targets[0].id] = child.value
            elif (
                isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
                and child is not node
            ):
                scope.functions[child.name] = child
        return scope

    # --- What a call reaches ------------------------------------------------------

    def _target(
        self, expr: ast.expr, scope: _Scope, seen: frozenset[tuple[str, str]]
    ) -> object:
        """What an expression stands for: a `_Callee`, `_Class`, `_Module` or `None`."""
        if isinstance(expr, ast.Name):
            return self._name_target(expr.id, scope, seen)
        if isinstance(expr, ast.Lambda):
            return _Callee(_Function(expr, scope.module, scope.cls, scope.self_cls))
        if isinstance(expr, ast.Attribute):
            return self._attribute_target(expr, scope, seen)
        if isinstance(expr, ast.Call) and expr.args:
            return self._wrapped_target(expr, scope, seen)
        return None

    def _name_target(
        self, name: str, scope: _Scope, seen: frozenset[tuple[str, str]]
    ) -> object:
        """What a bare name stands for; a parameter stands for nothing known."""
        if name in scope.params:
            return None
        if name in scope.values:
            key = (str(id(scope)), name)
            if key in seen:
                return None
            return self._target(scope.values[name], scope, seen | {key})
        if name in scope.functions:
            return _Callee(_Function(scope.functions[name], scope.module))
        if name in scope.imports:
            return self._imported(scope.module, scope.imports[name], seen)
        return self._member(scope.module, name, seen)

    def _attribute_target(
        self, expr: ast.Attribute, scope: _Scope, seen: frozenset[tuple[str, str]]
    ) -> object:
        """What `self.x`, `super().x`, `module.x` or `Class.x` stands for."""
        owner = expr.value
        if isinstance(owner, ast.Name) and owner.id == scope.instance:
            return scope.self_cls and self._class_member(
                scope.self_cls, expr.attr, scope.self_cls, set()
            )
        if (
            isinstance(owner, ast.Call)
            and isinstance(owner.func, ast.Name)
            and owner.func.id == "super"
            and "super" not in scope.names
        ):
            return scope.cls and self._base_member(
                scope.cls, expr.attr, scope.self_cls, set()
            )
        found = self._target(owner, scope, seen)
        if isinstance(found, _Module):
            return self._member(found, expr.attr, seen)
        if isinstance(found, _Class):
            return self._class_member(found, expr.attr, None, set())
        return None

    def _wrapped_target(
        self, expr: ast.Call, scope: _Scope, seen: frozenset[tuple[str, str]]
    ) -> _Callee | None:
        """The function a `partial(...)`, `staticmethod(...)` or `classmethod(...)` wraps.

        A `partial` keeps the arguments it gives.
        """
        wrapped = self._target(expr.args[0], scope, seen)
        if not isinstance(wrapped, _Callee):
            return None
        if qualified(expr.func, scope.names) == _PARTIAL:
            args = [(a, scope) for a in expr.args[1:] if not isinstance(a, ast.Starred)]
            keywords = [(k.arg, (k.value, scope)) for k in expr.keywords if k.arg]
            return _Callee(
                wrapped.function,
                (*wrapped.args, *args),
                (*wrapped.keywords, *keywords),
            )
        func = expr.func
        if (
            isinstance(func, ast.Name)
            and func.id in _METHOD_WRAPPERS
            and func.id not in scope.names
            and func.id not in scope.values
        ):
            return wrapped
        return None

    def _class_member(
        self, cls: _Class, name: str, self_cls: _Class | None, seen: set[_Class]
    ) -> object:
        """A method or callable attribute a class or its bases give a name."""
        if cls in seen:
            return None
        seen.add(cls)
        scope = self._module_scope(cls.module)
        for statement in cls.node.body:
            if (
                isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef)
                and statement.name == name
            ):
                return _Callee(_Function(statement, cls.module, cls, self_cls or cls))
            if isinstance(statement, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == name for t in statement.targets
            ):
                return self._target(statement.value, scope, frozenset())
        for statement in cls.node.body:
            if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
                found = self._set_on_instance(statement, cls, name)
                if found is not None:
                    return found
        return self._base_member(cls, name, self_cls, seen)

    def _set_on_instance(self, method: FunctionNode, cls: _Class, name: str) -> object:
        """The callable `self.<name> = ...` or `cls.<name> = ...` sets in a method."""
        method_scope = self._scope(method, cls.module, cls, cls)
        if method_scope.instance is None:
            return None
        for child in _body(method):
            if (
                isinstance(child, ast.Assign)
                and len(child.targets) == 1
                and isinstance(target := child.targets[0], ast.Attribute)
                and target.attr == name
                and isinstance(target.value, ast.Name)
                and target.value.id == method_scope.instance
            ):
                return self._target(child.value, method_scope, frozenset())
        return None

    def _base_member(
        self, cls: _Class, name: str, self_cls: _Class | None, seen: set[_Class]
    ) -> object:
        scope = self._module_scope(cls.module)
        for base in cls.node.bases:
            found_base = self._target(base, scope, frozenset())
            if isinstance(found_base, _Class):
                found = self._class_member(found_base, name, self_cls, seen)
                if found is not None:
                    return found
        return None

    # --- Answers ------------------------------------------------------------------

    def answer(self, function: _Function) -> _Answer:
        """Whether a function asserts, worked out once and kept with what it read.

        A function already being worked out up the call chain counts as not
        asserting there; a "no" that leaned on one isn't kept, a "yes" always is.
        """
        kept = self._answers.get(function)
        if kept is not None:
            for key in kept[1]:
                self._note(key)
            return kept[0]
        if function in self._open:
            self._reach = min(self._reach, self._open[function])
            return _NO
        depth = len(self._open)
        self._open[function] = depth
        outer_reach, self._reach = self._reach, _UNREACHED
        self._deps.append({function.module.key})
        try:
            found = self._work_out(function)
        finally:
            deps = self._deps.pop()
            del self._open[function]
            reach, self._reach = self._reach, outer_reach
        if found.asserts or reach >= depth:
            self._answers[function] = (found, frozenset(deps))
        else:
            self._reach = min(self._reach, reach)
        if self._deps:
            self._deps[-1].update(deps)
        return found

    def _work_out(self, function: _Function) -> _Answer:
        scope = self._scope(
            function.node, function.module, function.cls, function.self_cls
        )
        nodes = list(_body(function.node))
        if any(is_real_assertion(node, scope.names) for node in nodes):
            return _YES
        params: set[str] = set()
        for node in nodes:
            if not isinstance(node, ast.Call):
                continue
            if self.call_asserts(node, scope):
                return _YES
            if isinstance(node.func, ast.Name) and node.func.id in scope.params:
                params.add(node.func.id)
        return _Answer(asserts=False, calls_params=frozenset(params))

    def call_asserts(self, call: ast.Call, scope: _Scope) -> bool:
        """Whether a call reaches a function that asserts, given what it passes."""
        callee = self._target(call.func, scope, frozenset())
        if not isinstance(callee, _Callee):
            return False
        found = self.answer(callee.function)
        if found.asserts:
            return True
        if not found.calls_params:
            return False
        args = [
            *callee.args,
            *((a, scope) for a in call.args if not isinstance(a, ast.Starred)),
        ]
        keywords = dict(callee.keywords)
        keywords.update((k.arg, (k.value, scope)) for k in call.keywords if k.arg)
        callee_scope = self._scope(
            callee.function.node,
            callee.function.module,
            callee.function.cls,
            callee.function.self_cls,
        )
        for param in found.calls_params:
            arg = keywords.get(param)
            if arg is None and param in callee_scope.positional:
                index = callee_scope.positional.index(param)
                arg = args[index] if index < len(args) else None
            if arg is not None and self._passes_assertion(*arg):
                return True
        return False

    def _passes_assertion(self, expr: ast.expr, scope: _Scope) -> bool:
        """Whether an argument is an `assert*` function or a function that asserts."""
        name = _final_name(expr)
        if name is not None and name.lower().startswith("assert"):
            return True
        callee = self._target(expr, scope, frozenset())
        return isinstance(callee, _Callee) and self.answer(callee.function).asserts

    # --- A test file's view -------------------------------------------------------

    def assertions(self, path: Path, tree: ast.Module) -> "Assertions":
        """What one test file's tests assert, following their calls into the tree."""
        key = absolute(path)
        module = self.module(key, tree)
        if module is None:  # pragma: no cover  # A tree handed in always reads.
            raise ValueError(key)
        return Assertions(self, module)

    def test_calls_assert(
        self, test: TestFunction, module: _Module, calls: list[ast.Call]
    ) -> tuple[bool, set[str]]:
        """Whether any of a test's calls reaches a function that asserts.

        Returns:
            The answer, and every module it relied on.
        """
        cls = _Class(test.classes[-1], module) if test.classes else None
        scope = self._scope(test.node, module, cls, cls, dict(test.imports))
        if instance_param(test) is None:
            scope.instance = None
            scope.self_cls = None
        keys: set[str] = set()
        self._deps.append(keys)
        try:
            found = any(self.call_asserts(call, scope) for call in calls)
        finally:
            self._deps.pop()
        return found, keys


class Assertions:
    """Whether a test file's tests hold real assertions, following their calls.

    Made by `TestTree.assertions`, one per test file; checks reach it on
    `TestFile.assertions`.
    """

    def __init__(self, tree: TestTree, module: _Module) -> None:
        """A test file's view of the tree, the file itself being `module`."""
        self._tree = tree
        self._module = module
        self._followed: set[str] = set()

    def holds(self, test: TestFunction, nodes: Iterable[ast.AST] | None = None) -> bool:
        """Whether a test, or the given nodes of it, hold a real assertion.

        A real assertion is one `is_real_assertion` sees, or a call into a function
        of the test tree that makes one.

        Args:
            test: The test.
            nodes: Some of the test's nodes, such as one statement's; by default
                its whole body (`walk_test`).
        """
        seen = list(walk_test(test) if nodes is None else nodes)
        if any(is_real_assertion(node, test.imports) for node in seen):
            return True
        calls = [node for node in seen if isinstance(node, ast.Call)]
        if not calls:
            return False
        found, keys = self._tree.test_calls_assert(test, self._module, calls)
        self._followed |= keys
        return found

    @property
    def followed(self) -> dict[str, str]:
        """Every other module an answer relied on, by absolute path, with its digest.

        A module looked for in the test tree and not found is here too, with an
        empty digest, so the result goes stale when it appears.
        """
        return {
            key: self._tree.digest(key)
            for key in sorted(self._followed)
            if key != self._module.key
        }
