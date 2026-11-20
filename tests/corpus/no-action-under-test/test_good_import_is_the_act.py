"""Near-misses: an `import` in the test body runs the module, so it is the act
(#178). Modelled on networkx `tests/test_import.py:9` and pandas
`test_register_accessor.py:128`. Analysed, never run.
"""

import pytest

pytestmark = pytest.mark.unit


def test_from_import_is_the_act():
    from networkx import networkx

    assert networkx.__name__ == "networkx.networkx"


def test_import_inside_warns_is_the_act():
    with pytest.warns(DeprecationWarning, match="moved"):
        import app.legacy  # noqa: F401


def test_stdlib_import_runs_code_too():
    import os.path

    assert os.path.sep == "/"


def test_importorskip_imports_like_a_statement():
    legacy = pytest.importorskip("app.legacy")
    assert legacy.VERSION == "1"
