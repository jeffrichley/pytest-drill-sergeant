"""Near-misses: no call, but the assertion reads a name imported from outside the
standard library, which runs the code under test (#178). Modelled on networkx
`test_distance_measures.py:607`, pandas `test_na_scalar.py:227`, httpx
`test_status_codes.py:14` and bookwright `test_contract.py:152`. Analysed, never run.
"""

import httpx
import networkx as nx
import pytest
from app import contract
from pandas import NA

from . import shapes

pytestmark = pytest.mark.unit


def test_alias_by_attribute():
    assert nx.barycenter is nx.centroid


def test_operator_on_an_imported_value():
    assert (~NA) is NA


def test_subscript_on_an_imported_enum():
    assert httpx.codes["NOT_FOUND"] == 404


def test_project_constant_by_attribute():
    assert contract.DOC_TYPES[0] == "memo"


def test_iterates_an_imported_value():
    assert [kind for kind in contract.DOC_TYPES] == ["memo"]


def test_relative_import_is_the_project():
    assert shapes.ASIDE_SHAPE["kind"] == "aside"
