"""The cache: per-file results kept between runs, so a warm run reads, not parses.

One JSON file in a directory the front end names (under pytest's cache directory)
holds one entry per test file, by the file's resolved path. An entry is the file's
per-file result and the key it was made under: the hash of the file's bytes, plus
drill-sergeant's own code (which fixes its version), plus the config that shapes per-file
analysis. A key that no longer matches, or an entry that doesn't read back, is
simply a miss: the file is analysed again and its entry replaced.

The cache is the one file a run writes. It is written only when an entry changed,
in one atomic replace, so a run racing another (the CLI beside the plugin) never
reads half a file; the later writer's entries win.

Results are stored as plain JSON, never pickled, so reading a cache that came with
a checkout can't run code. Any dataclass of plain fields round-trips: it is written
as the list of its fields' values and read back by its type hints, so a field added
to a cached dataclass needs nothing here.
"""

import dataclasses
import enum
import functools
import hashlib
import json
import os
import tempfile
import types
import typing
from collections.abc import Callable, Hashable, Mapping
from pathlib import Path
from typing import Any, TypeVar

_T = TypeVar("_T")

# The cache's directory name under pytest's cache directory, where pytest's
# `cache.mkdir` puts it: `<cache_dir>/d/drill-sergeant`. The CLI finds it there too.
CACHE_NAME = "drill-sergeant"

# The file under the cache directory that holds every entry.
_STORE = "results.json"

# Errors that mean an entry didn't read back as the type it should be.
_UNREADABLE = (TypeError, ValueError, LookupError, AttributeError)


def encode(value: object) -> object:
    """A value as plain JSON data: a dataclass as the list of its fields' values."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return [
            encode(getattr(value, f.name)) for f in dataclasses.fields(value) if f.init
        ]
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return [[encode(k), encode(v)] for k, v in value.items()]
    if isinstance(value, tuple | list | frozenset | set):
        return [encode(item) for item in value]
    if value is None or isinstance(value, str | int | float):
        return value
    raise TypeError(f"cannot cache a {type(value).__name__}")


def _exactly(kind: type) -> Callable[[object], object]:
    def read(data: object) -> object:
        if type(data) is not kind:
            raise TypeError(f"expected {kind.__name__}, got {type(data).__name__}")
        return data

    return read


def _items(data: object) -> list[Any]:
    if not isinstance(data, list):
        raise TypeError(f"expected a list, got {type(data).__name__}")
    return data


@functools.cache
def _decoder(kind: object) -> Callable[[Any], Any]:  # noqa: PLR0911  # One branch per kind of type, each a line or two.
    """How to read back a value of a type from what `encode` wrote.

    Raises:
        TypeError: When the type isn't one `encode` writes.
    """
    origin, args = typing.get_origin(kind), typing.get_args(kind)
    if dataclasses.is_dataclass(kind) and isinstance(kind, type):
        hints = typing.get_type_hints(kind)
        fields = [_decoder(hints[f.name]) for f in dataclasses.fields(kind) if f.init]
        cls = kind
        return lambda data: cls(
            *[read(v) for read, v in zip(fields, _items(data), strict=True)]
        )
    if origin in {types.UnionType, typing.Union} and type(None) in args:
        [other] = [a for a in args if a is not type(None)]
        read = _decoder(other)
        return lambda data: None if data is None else read(data)
    if origin is tuple and len(args) == 2 and args[1] is Ellipsis:  # noqa: PLR2004  # tuple[X, ...]
        item = _decoder(args[0])
        return lambda data: tuple(item(v) for v in _items(data))
    if origin is tuple:
        reads = [_decoder(a) for a in args]
        return lambda data: tuple(
            r(v) for r, v in zip(reads, _items(data), strict=True)
        )
    if origin in {list, frozenset, set}:
        item, collection = _decoder(args[0]), origin
        return lambda data: collection(item(v) for v in _items(data))
    if origin in {dict, Mapping}:
        key, value = _decoder(args[0]), _decoder(args[1])
        return lambda data: {key(k): value(v) for k, v in _items(data)}
    if isinstance(kind, type) and issubclass(kind, enum.Enum):
        return kind
    if kind is Path:
        return Path
    if kind in {str, int, float, bool}:
        return _exactly(kind)
    raise TypeError(f"cannot read back a cached {kind!r}")


def decode(kind: type[_T], data: object) -> _T:
    """A value of a type, read back from what `encode` wrote.

    Raises:
        TypeError: When the data isn't one of that type.
        ValueError: When the data isn't one of that type.
    """
    # A type is hashable, though `type[_T]` doesn't say so.
    value: _T = _decoder(typing.cast(Hashable, kind))(data)
    return value


@functools.cache
def _code_fingerprint() -> str:
    """A digest of drill-sergeant's own source, so any change to it is a new key.

    A released version always changes it; an unreleased edit does too.
    """
    package = Path(__file__).parent
    digest = hashlib.blake2b(digest_size=16)
    for path in sorted(package.rglob("*.py")):
        digest.update(path.relative_to(package).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def content_hash(source: bytes) -> str:
    """The hash of a file's bytes, as a cache key holds it."""
    return hashlib.blake2b(source, digest_size=16).hexdigest()


def context(settings: object) -> str:
    """The part of a cache key every file shares in one run.

    It holds drill-sergeant's own code, which stands for its version and is finer
    (reading the installed version costs more than the whole warm run), and the
    settings that shape per-file analysis, given as plain data.
    """
    text = json.dumps([_code_fingerprint(), encode(settings)])
    return hashlib.blake2b(text.encode(), digest_size=16).hexdigest()


class Cache:
    """The entries in one cache directory, read once and written back once."""

    def __init__(self, directory: Path) -> None:
        """Read the entries in a directory; an unreadable store reads as empty.

        Args:
            directory: The directory the store is in; made when it is first
                written.
        """
        self.directory = directory
        self._entries: dict[str, Any] = {}
        self._changed = False
        try:
            entries = json.loads((directory / _STORE).read_bytes())
        except (OSError, ValueError):
            return
        if isinstance(entries, dict):
            self._entries = entries

    def get(self, path: Path, key: str, kind: type[_T]) -> _T | None:
        """A file's cached result, or `None` when its entry is missing or stale.

        An entry that doesn't read back as `kind` is a miss, as a stale one is.
        """
        entry = self._entries.get(str(path.resolve()))
        if not isinstance(entry, list) or len(entry) != 2 or entry[0] != key:  # noqa: PLR2004  # An entry is [key, result].
            return None
        try:
            return decode(kind, entry[1])
        except _UNREADABLE:
            return None

    def put(self, path: Path, key: str, result: object) -> None:
        """Keep a file's result under its key, replacing its old entry."""
        self._entries[str(path.resolve())] = [key, encode(result)]
        self._changed = True

    def save(self) -> None:
        """Write the entries back, when any changed, in one atomic replace.

        Entries for files that no longer exist are dropped. A cache that can't be
        written is left as it was: the run goes on uncached.
        """
        if not self._changed:
            return
        entries = {p: e for p, e in self._entries.items() if Path(p).exists()}
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            handle, name = tempfile.mkstemp(dir=self.directory, prefix=".results-")
        except OSError:
            return
        temp = Path(name)
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as out:
                json.dump(entries, out, separators=(",", ":"))
            temp.replace(self.directory / _STORE)
        except OSError:
            temp.unlink(missing_ok=True)
