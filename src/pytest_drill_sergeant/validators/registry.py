"""Validator registry for drill-sergeant."""

from __future__ import annotations

from collections.abc import Callable  # noqa: TC003
from dataclasses import dataclass

from pytest_drill_sergeant.validators.aaa import AAAValidator
from pytest_drill_sergeant.validators.base import Validator
from pytest_drill_sergeant.validators.file_length import FileLengthValidator
from pytest_drill_sergeant.validators.marker import MarkerValidator


@dataclass(frozen=True)
class ValidatorDefinition:
    """Defines a registered validator and how to construct it."""

    name: str
    factory: Callable[[], Validator]


DEFAULT_VALIDATOR_REGISTRY: tuple[ValidatorDefinition, ...] = (
    ValidatorDefinition(name="marker", factory=MarkerValidator),
    ValidatorDefinition(name="aaa", factory=AAAValidator),
    ValidatorDefinition(name="file_length", factory=FileLengthValidator),
)


def build_validators() -> list[tuple[str, Validator]]:
    """Build validator instances from registry definitions."""
    return [(definition.name, definition.factory()) for definition in DEFAULT_VALIDATOR_REGISTRY]
