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
take the call's return type. A call to a function imported from a third-party
package, a module found neither under the project nor in the standard library,
nor pytest's, is code the check can't see: it may assert, so it counts as one.

An absolute import is looked for under each directory above the importing file,
nearest first, and the `src/` in each, up to the project root, as pytest's
rootdir-style `sys.path` finds it, then in the production source dirs; the first
file found is the module, followed only when it is in the test tree. In a flat
layout, production modules beside the tests are in the tree.

What a call is, a function or a class (`Assertions.definition`), is read from its
definition the same way, with one difference: the definition may be in production
code too, anywhere under the project. A builtin name nothing rebinds is Python's
own; a call the files don't show the definition of is not known.

Each function's answer is worked out once per run and kept with the modules it
relied on, so a test file's result can name every module it followed (`followed`)
for the cache to check.
"""

import ast
import builtins
import os
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from pytest_drill_sergeant.cache import content_hash
from pytest_drill_sergeant.checks.ast_tools import (
    EXPECT_FUNCTIONS,
    KNOWN_PACKAGES,
    bound_names,
    imports_seen_by,
    instance_param,
    is_collected_function,
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
_SRC = "src"
_MISSING = ""
_OUTSIDE = "outside"

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
        star: Whether its top level imports `*`, which may bind any name.
    """

    key: str
    names: dict[str, str]
    bindings: dict[str, "_Binding"]
    star: bool = False


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


# What an expression can stand for: a function to call, a class, a module, or
# nothing known.
_Target = _Callee | _Class | _Module | None

# What a module's top-level name is bound to: an import, a `def`, a `class` or a
# value.
_Binding = _Import | FunctionNode | ast.ClassDef | ast.expr


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


class CallKind(Enum):
    """What a call is, by its definition."""

    FUNCTION = auto()
    CLASS = auto()  # A constructor: a class's call makes an instance.
    UNKNOWN = auto()  # The files don't show its definition.


@dataclass(frozen=True)
class Definition:
    """What a call is, and its definition when the files show one.

    Attributes:
        kind: Function, class or not known.
        node: The function's `def` or lambda, or the `class`; `None` for a
            builtin or a call not known.
        builtin: The builtin's name, when the call is Python's own.
    """

    kind: CallKind
    node: FunctionNode | ast.Lambda | ast.ClassDef | None = None
    builtin: str | None = None


_UNKNOWN = Definition(CallKind.UNKNOWN)

_NO = _Answer(asserts=False)
_YES = _Answer(asserts=True)
_NO_CYCLE = 1 << 30


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


def _bindings(tree: ast.Module) -> dict[str, _Binding]:
    bindings: dict[str, _Binding] = {}
    for statement in _top_level(tree.body):
        if isinstance(statement, ast.Import | ast.ImportFrom):
            bindings.update(_import_bindings(statement))
        elif isinstance(
            statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ):
            bindings[statement.name] = statement
        elif (assigned := _plain_assignment(statement)) is not None:
            bindings[assigned[0]] = assigned[1]
        elif not isinstance(statement, ast.If | ast.Try):
            for name in bound_names(statement):
                bindings.pop(name, None)
    return bindings


def _plain_assignment(node: ast.AST) -> tuple[str, ast.expr] | None:
    """The name and value of a `name = value` statement, or `None` for any other."""
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    ):
        return node.targets[0].id, node.value
    return None


def _is_static(node: FunctionNode | ast.Lambda, names: dict[str, str]) -> bool:
    """Whether a function is decorated with the builtin `staticmethod`."""
    return (
        isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and "staticmethod" not in names
        and any(
            isinstance(d, ast.Name) and d.id == "staticmethod"
            for d in node.decorator_list
        )
    )


def _body(node: FunctionNode | ast.Lambda) -> Iterator[ast.AST]:
    """Every node of a function's body, at any depth."""
    if isinstance(node, ast.Lambda):
        yield from ast.walk(node.body)
        return
    for statement in node.body:
        yield from ast.walk(statement)


def _is_builtin(name: str, scope: _Scope, node: FunctionNode) -> bool:
    """Whether a name is Python's builtin: one nothing in the function or module binds.

    A module that imports `*` may bind any name, so no name is surely a builtin
    there.
    """
    return (
        hasattr(builtins, name)
        and not scope.module.star
        and name not in scope.params
        and name not in scope.imports
        and name not in scope.names
        and name not in scope.module.bindings
        and not any(_binds(child, name) for child in _body(node))
    )


def _binds(node: ast.AST, name: str) -> bool:
    """Whether a node binds a name: a target, a `def`, a `class` or `except ... as`."""
    if isinstance(node, ast.Name):
        return isinstance(node.ctx, ast.Store) and node.id == name
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return node.name == name
    return isinstance(node, ast.ExceptHandler) and node.name == name


def _binds_in_scope(node: ast.AST, name: str) -> bool:
    """Whether a statement binds a name in the scope it runs in.

    A `def` or `class` binds its own name; what is inside one is its own scope. An
    import binds what it names.
    """
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return node.name == name
    if isinstance(node, ast.Import | ast.ImportFrom):
        return any(
            (alias.asname or alias.name.split(".")[0]) == name for alias in node.names
        )
    return _binds(node, name) or any(
        _binds_in_scope(child, name) for child in ast.iter_child_nodes(node)
    )


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
        self,
        test_files: Iterable[Path],
        production: Iterable[Path] = (),
        root: Path | None = None,
    ) -> None:
        """A run's test tree.

        Args:
            test_files: The run's test files; their directories, and every
                directory below them, are in the tree.
            production: Production code: files, and directories whose every file
                is, kept out of the tree. A module is looked for in each
                directory too.
            root: The project root: an absolute import from a file under it is
                looked for no higher.
        """
        self._dirs = {os.path.dirname(absolute(p)) for p in test_files}
        self._root = absolute(root) if root is not None else None
        self._production_files: set[str] = set()
        self._production_dirs: list[str] = []
        self._source_dirs: list[str] = []
        for path in production:
            key = absolute(path)
            if path.is_dir():
                self._production_dirs.append(key.rstrip(os.sep) + os.sep)
                self._source_dirs.append(key)
            else:
                self._production_files.add(key)
        self._project_modules: dict[tuple[str, str], tuple[bool, tuple[str, ...]]] = {}
        self._modules: dict[str, _Module | None] = {}
        self._files: dict[str, bool] = {}
        self._digests: dict[str, str] = {}
        self._resolved: dict[
            tuple[str, str, int, bool], tuple[_Module | None, tuple[str, ...]]
        ] = {}
        # Whether an import may resolve into production code: only while reading
        # what a call is (`definition`), never while following it for assertions.
        self._anywhere = False
        self._answers: dict[_Function, tuple[_Answer, frozenset[str]]] = {}
        # The functions being worked out, each at its depth in the call chain, and
        # the shallowest of them the answer now being worked out met again.
        self._in_progress: dict[_Function, int] = {}
        self._lowest_cycle = _NO_CYCLE
        self._deps: list[set[str]] = []
        self._resolving: set[int] = set()

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
        """A module's content hash, marked `outside` when it isn't in the tree; empty when it is missing.

        A cached result followed each module under its digest; any change means
        the result is stale. A module outside the tree is hashed too, as a
        definition read there (`definition`) is part of the result.
        """
        known = self._digests.get(key)
        if known is None:
            known = _MISSING
            if self._is_file(key):
                try:
                    known = content_hash(Path(key).read_bytes())
                except OSError:
                    known = _MISSING
                else:
                    if not self.contains(key):
                        known = f"{_OUTSIDE}:{known}"
            self._digests[key] = known
        return known

    def _absolute_bases(self, start: str) -> list[str]:
        """Where an absolute import from a file in `start` is looked for, in order.

        Each directory from `start` up, stopping at the project root when `start`
        is under it, and the `src/` in each; then the production source dirs.
        """
        ups = [start]
        while (parent := os.path.dirname(ups[-1])) != ups[-1] and ups[-1] != self._root:
            ups.append(parent)
        bases = [b for up in ups for b in (up, os.path.join(up, _SRC))]
        return [*bases, *self._source_dirs]

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
                key=key,
                names=module_imports(parsed),
                bindings=_bindings(parsed),
                star=any(
                    isinstance(s, ast.ImportFrom)
                    and any(a.name == "*" for a in s.names)
                    for s in _top_level(parsed.body)
                ),
            )
        self._modules[key] = found
        return found

    def _resolve(self, dotted: str, level: int, origin: _Module) -> _Module | None:
        """The module an import names, when it is a file of the test tree.

        While reading what a call is, a file of production code too.
        """
        start = os.path.dirname(origin.key)
        memo_key = (start, dotted, level, self._anywhere)
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
            bases = self._absolute_bases(start)
        noted: list[str] = []
        for base in bases:
            stem = os.path.join(base, *parts)
            candidates = (
                [stem + ".py", os.path.join(stem, _INIT)]
                if parts
                else [os.path.join(stem, _INIT)]
            )
            for candidate in candidates:
                noted.append(candidate)
                if self._is_file(candidate):
                    seen = self._anywhere or self.contains(candidate)
                    found = self.module(candidate) if seen else None
                    return found, tuple(noted)
        return None, tuple(noted)

    # --- Code the check can't see ---------------------------------------------------

    def _in_project(self, top: str, start: str) -> bool:
        """Whether a top-level module resolves under the project, from a file in `start`.

        It does when a `<top>.py` file or a `<top>/` package is found where
        `_absolute_bases` looks.
        """
        memo_key = (start, top)
        if memo_key not in self._project_modules:
            noted: list[str] = []
            found = False
            for base in self._absolute_bases(start):
                stem = os.path.join(base, top)
                noted += [stem + ".py", os.path.join(stem, _INIT)]
                if self._is_file(stem + ".py") or os.path.isdir(stem):
                    found = True
                    break
            self._project_modules[memo_key] = (found, tuple(noted))
        found, noted_keys = self._project_modules[memo_key]
        for key in noted_keys:
            self._note(key)
        return found

    def _calls_unseen_code(self, func: ast.expr, scope: _Scope) -> bool:
        """Whether a call goes into a third-party package, which may assert.

        That is a function reached through an import whose top-level module
        resolves neither under the project nor to the standard library, nor to
        pytest, whose functions drill-sergeant knows.
        """
        root = func
        while isinstance(root, ast.Attribute):
            root = root.value
        if not isinstance(root, ast.Name):
            return False
        # Playwright's `expect` is known too: it asserts only through a matcher.
        # The imported names the code sees, shadows gone; a relative import is
        # never in them, being the project's own.
        imported = scope.names.get(root.id)
        if imported is None or qualified(func, scope.names) in EXPECT_FUNCTIONS:
            return False
        top = imported.split(".")[0]
        return not (
            top in sys.stdlib_module_names
            or top in KNOWN_PACKAGES
            or self._in_project(top, os.path.dirname(scope.module.key))
        )

    def _member(  # noqa: PLR0911  # One return per kind of binding.
        self, module: _Module, name: str, seen: frozenset[tuple[str, str]]
    ) -> _Target:
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
    ) -> _Target:
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
            and not _is_static(node, module.names)
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
            elif (assigned := _plain_assignment(child)) is not None:
                scope.values[assigned[0]] = assigned[1]
            elif (
                isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
                and child is not node
            ):
                scope.functions[child.name] = child
        return scope

    def _scope_of(self, function: _Function) -> _Scope:
        return self._scope(
            function.node, function.module, function.cls, function.self_cls
        )

    # --- What a call reaches ------------------------------------------------------

    def _target(
        self, expr: ast.expr, scope: _Scope, seen: frozenset[tuple[str, str]]
    ) -> _Target:
        """What an expression stands for: a `_Callee`, `_Class`, `_Module` or `None`.

        An expression met again while it is still being worked out
        (`self.x = wrap(self.x)`) stands for nothing known.
        """
        if isinstance(expr, ast.Lambda):
            return _Callee(_Function(expr, scope.module, scope.cls, scope.self_cls))
        if id(expr) in self._resolving:
            return None
        self._resolving.add(id(expr))
        try:
            if isinstance(expr, ast.Name):
                return self._name_target(expr.id, scope, seen)
            if isinstance(expr, ast.Attribute):
                return self._attribute_target(expr, scope, seen)
            if isinstance(expr, ast.Call) and expr.args:
                return self._wrapped_target(expr, scope, seen)
            return None
        finally:
            self._resolving.discard(id(expr))

    def _name_target(
        self, name: str, scope: _Scope, seen: frozenset[tuple[str, str]]
    ) -> _Target:
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
    ) -> _Target:
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
        func = expr.func
        is_partial = qualified(func, scope.names) == _PARTIAL
        is_method_wrapper = (
            isinstance(func, ast.Name)
            and func.id in _METHOD_WRAPPERS
            and func.id not in scope.names
            and func.id not in scope.values
        )
        if not (is_partial or is_method_wrapper):
            return None
        wrapped = self._target(expr.args[0], scope, seen)
        if not isinstance(wrapped, _Callee):
            return None
        if is_partial:
            args = [(a, scope) for a in expr.args[1:] if not isinstance(a, ast.Starred)]
            keywords = [(k.arg, (k.value, scope)) for k in expr.keywords if k.arg]
            return _Callee(
                wrapped.function,
                (*wrapped.args, *args),
                (*wrapped.keywords, *keywords),
            )
        return wrapped

    def _class_member(
        self, cls: _Class, name: str, self_cls: _Class | None, seen: set[_Class]
    ) -> _Target:
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

    def _set_on_instance(self, method: FunctionNode, cls: _Class, name: str) -> _Target:
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
    ) -> _Target:
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
        if function in self._in_progress:
            self._lowest_cycle = min(self._lowest_cycle, self._in_progress[function])
            return _NO
        depth = len(self._in_progress)
        self._in_progress[function] = depth
        outer_cycle, self._lowest_cycle = self._lowest_cycle, _NO_CYCLE
        self._deps.append({function.module.key})
        try:
            found = self._work_out(function)
        finally:
            deps = self._deps.pop()
            del self._in_progress[function]
            cycle, self._lowest_cycle = self._lowest_cycle, outer_cycle
        if found.asserts or cycle >= depth:
            self._answers[function] = (found, frozenset(deps))
        else:
            self._lowest_cycle = min(self._lowest_cycle, cycle)
        if self._deps:
            self._deps[-1].update(deps)
        return found

    def _work_out(self, function: _Function) -> _Answer:
        scope = self._scope_of(function)
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

    def call_asserts(
        self, call: ast.Call, scope: _Scope, *, unseen: bool = True
    ) -> bool:
        """Whether a call reaches a function that asserts, given what it passes.

        With `unseen`, a call into a third-party package, code the check can't
        see, may assert, so it counts; without, only a function the files show
        does.
        """
        callee = self._target(call.func, scope, frozenset())
        if not isinstance(callee, _Callee):
            return unseen and self._calls_unseen_code(call.func, scope)
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
        callee_scope = self._scope_of(callee.function)
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
        self,
        test: TestFunction,
        module: _Module,
        calls: list[ast.Call],
        *,
        unseen: bool = True,
    ) -> tuple[bool, set[str]]:
        """Whether any of a test's calls reaches a function that asserts.

        `unseen` is as `call_asserts` takes it.

        Returns:
            The answer, and every module it relied on.
        """
        scope = self._test_scope(test, module)
        keys: set[str] = set()
        self._deps.append(keys)
        try:
            found = any(self.call_asserts(call, scope, unseen=unseen) for call in calls)
        finally:
            self._deps.pop()
        return found, keys

    def definition(
        self, test: TestFunction, module: _Module, call: ast.Call
    ) -> tuple[Definition, set[str]]:
        """What a call in a test is, read from its definition.

        The definition may be in the test tree or in production code. A builtin
        name the test and its module don't rebind is Python's own: a class when
        it is a type (`str`), else a function (`len`).

        Returns:
            The definition, and every module it relied on.
        """
        scope = self._test_scope(test, module)
        keys: set[str] = set()
        self._deps.append(keys)
        self._anywhere = True
        try:
            target = self._target(call.func, scope, frozenset())
        finally:
            self._anywhere = False
            self._deps.pop()
        if isinstance(target, _Callee):
            return Definition(CallKind.FUNCTION, target.function.node), keys
        if isinstance(target, _Class):
            return Definition(CallKind.CLASS, target.node), keys
        func = call.func
        if isinstance(func, ast.Name) and _is_builtin(func.id, scope, test.node):
            is_type = isinstance(getattr(builtins, func.id), type)
            kind = CallKind.CLASS if is_type else CallKind.FUNCTION
            return Definition(kind, builtin=func.id), keys
        return _UNKNOWN, keys

    def overrides_inherited_test(
        self, test: TestFunction, module: _Module
    ) -> tuple[bool, set[str]]:
        """Whether a test method overrides a test a base class of its class defines.

        Its class's bases are read through the classes around it and the module's
        imports into the test tree, at any depth; a base the files don't show
        (third-party, the standard library, a module not found) defines nothing
        here. The bases are walked depth first, left to right, and the first that
        binds the name in its body decides: it defines the test when that binding
        is a `def` pytest collects, and not when it is anything else (a fixture, an
        assignment), which hides any test further up.

        Returns:
            The answer, and every module it relied on.
        """
        if not test.classes:
            return False, set()
        keys: set[str] = set()
        self._deps.append(keys)
        try:
            found = self._inherited_binding(
                _Class(test.classes[-1], module),
                test.node.name,
                test.classes[:-1],
                set(),
            )
        finally:
            self._deps.pop()
        inherits = found is not None and is_collected_function(*found)
        return inherits, keys

    def _inherited_binding(
        self,
        cls: _Class,
        name: str,
        around: tuple[ast.ClassDef, ...],
        seen: set[_Class],
    ) -> tuple[ast.stmt, dict[str, str]] | None:
        """The first statement a base of `cls` binds `name` with, and its module's imports.

        `around` are the classes `cls` is defined in, outermost first: a base named
        bare may be a class one of their bodies defines.
        """
        scope = self._module_scope(cls.module)
        for base_expr in cls.node.bases:
            base = self._around(base_expr, around, cls.module) or self._target(
                base_expr, scope, frozenset()
            )
            if not isinstance(base, _Class) or base in seen:
                continue
            seen.add(base)
            binding = next(
                (s for s in base.node.body if _binds_in_scope(s, name)), None
            )
            if binding is not None:
                return binding, base.module.names
            found = self._inherited_binding(base, name, (), seen)
            if found is not None:
                return found
        return None

    @staticmethod
    def _around(
        expr: ast.expr, around: tuple[ast.ClassDef, ...], module: _Module
    ) -> _Class | None:
        """The class a bare name stands for in the bodies of the classes around."""
        if not isinstance(expr, ast.Name):
            return None
        for outer in reversed(around):
            for statement in outer.body:
                if isinstance(statement, ast.ClassDef) and statement.name == expr.id:
                    return _Class(statement, module)
        return None

    def _test_scope(self, test: TestFunction, module: _Module) -> _Scope:
        cls = _Class(test.classes[-1], module) if test.classes else None
        scope = self._scope(test.node, module, cls, cls, dict(test.imports))
        if instance_param(test) is None:
            scope.instance = None
            scope.self_cls = None
        return scope


class Assertions:
    """Whether a test file's tests hold real assertions, and what their calls are.

    Made by `TestTree.assertions`, one per test file; checks reach it on
    `TestFile.assertions`.
    """

    def __init__(self, tree: TestTree, module: _Module) -> None:
        """A test file's view of the tree, the file itself being `module`."""
        self._tree = tree
        self._module = module
        self._followed: set[str] = set()

    def holds(
        self,
        test: TestFunction,
        nodes: Iterable[ast.AST] | None = None,
        *,
        unseen: bool = True,
    ) -> bool:
        """Whether a test, or the given nodes of it, hold a real assertion.

        A real assertion is one `is_real_assertion` sees, or a call into a function
        of the test tree that makes one; with `unseen`, a call into a third-party
        package, which may, counts too.

        Args:
            test: The test.
            nodes: Some of the test's nodes, such as one statement's; by default
                its whole body (`walk_test`).
            unseen: Whether a call into a third-party package counts.
        """
        seen = list(walk_test(test) if nodes is None else nodes)
        if any(is_real_assertion(node, test.imports) for node in seen):
            return True
        calls = [node for node in seen if isinstance(node, ast.Call)]
        if not calls:
            return False
        found, keys = self._tree.test_calls_assert(
            test, self._module, calls, unseen=unseen
        )
        self._followed |= keys
        return found

    def definition(self, test: TestFunction, call: ast.Call) -> Definition:
        """What a call in a test is: a function, a class, or not known.

        Read from its definition in the test tree or production code, or as a
        builtin; never from its name.
        """
        found, keys = self._tree.definition(test, self._module, call)
        self._followed |= keys
        return found

    def overrides_inherited_test(self, test: TestFunction) -> bool:
        """Whether a test method overrides a test a base class of its class defines.

        Read from the bases' definitions in the test tree; a base it can't see
        defines nothing. Never from a name.
        """
        found, keys = self._tree.overrides_inherited_test(test, self._module)
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
