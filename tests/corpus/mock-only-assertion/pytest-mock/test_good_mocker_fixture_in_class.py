"""Near-misses: the project declares pytest-mock, but the class around these tests
defines its own `module_mocker` fixture, by `name=`. Analysed, never run."""

import pytest
from shop import FakePatcher, reindex

pytestmark = pytest.mark.unit


class TestReindex:
    @pytest.fixture(name="module_mocker")
    def own_patcher(self):
        return FakePatcher()

    def test_reindex_flag(self, module_mocker):
        rebuild = module_mocker.patch("shop.rebuild")
        reindex()
        assert rebuild.called
