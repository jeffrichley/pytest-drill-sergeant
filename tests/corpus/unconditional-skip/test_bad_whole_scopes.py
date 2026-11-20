"""A class and a module skipped on every run, through aliases.

Analysed, never run.
"""

import pytest as pt
from pytest import mark
from search import Index

pt.skip("search is being rewritten", allow_module_level=True)  # expect: DS402

pytestmark = [mark.skip(reason="search is being rewritten"), mark.unit]  # expect: DS402


@pt.mark.skip(reason="ranking changed")  # expect: DS402
class TestIndex:
    def test_index_finds_an_exact_match(self):
        assert Index(["ada"]).find("ada") == ["ada"]

    def test_index_builds_from_a_list(self):
        Index(["ada", "bob"]).rebuild()


def test_index_loads_from_disk(tmp_path):
    Index.load(tmp_path)
