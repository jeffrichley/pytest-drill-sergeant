"""Internal helpers for pytest hook implementations.

This module exposes pure functions that operate on abstract sequences of
``_pytest.nodes.Item`` objects. The public pytest hook consumes and mutates
``list[Item]`` at the boundary while internals rely on ``Sequence[Item]``
for read-only access.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imports for type checking only
    from collections.abc import Sequence

    from _pytest.nodes import Item


def plan_item_order(items: Sequence[Item]) -> list[Item]:
    """Return a new list of items in the desired execution order.

    The function is pure: it never mutates ``items`` and always returns a
    new list. The current policy performs a stable sort by ``nodeid``.
    """
    return sorted(items, key=lambda i: i.nodeid)
