"""The cache, through the engine seam: per-file results reused while a file's bytes,
drill-sergeant and the config that shapes per-file analysis stay the same."""

import pytest

from pytest_drill_sergeant.engine import Config, inspect
from pytest_drill_sergeant.findings import Level

pytestmark = pytest.mark.unit


MOCK_SETUP_OF_THREE = (
    "from unittest import mock\n"
    "\n"
    "def test_total():\n"
    "    repo = mock.create_autospec(Repo, instance=True)\n"
    "    repo.find.return_value = [1, 2]\n"
    "    repo.count.return_value = 2\n"
    "    assert total(repo) == 3\n"
)
# DS303 is off by default until it is proven.
MOCK_SETUP_ON = {"DS303": Level.FAIL}


def test_warm_run_finds_what_an_uncached_run_finds(golden_suite, cache_dir):
    """Over the golden suite: small, fixed, and with findings in it."""
    files = golden_suite
    inspect(files, Config(), cache_dir=cache_dir)

    warm = inspect(files, Config(), cache_dir=cache_dir)

    assert warm == inspect(files, Config(cache=False))


def test_warm_run_with_nothing_changed_writes_nothing(
    unseeded_random_test, cache_dir, watch
):
    inspect([unseeded_random_test], Config(), cache_dir=cache_dir)
    written = watch(cache_dir)

    inspect([unseeded_random_test], Config(), cache_dir=cache_dir)

    assert any(cache_dir.iterdir())
    assert written() == []


def test_changed_file_is_analysed_again(write_test_file, cache_dir, unit_mark):
    path = write_test_file("def test_it():\n    assert run() == 1\n")
    inspect([path], Config(), cache_dir=cache_dir)
    path.write_text(
        "import random\n\ndef test_it():\n    assert random.random() < 2\n" + unit_mark
    )

    findings = inspect([path], Config(), cache_dir=cache_dir).findings

    assert [(f.code, f.line) for f in findings] == [("DS803", 4)]


def test_corrupt_cache_is_rebuilt_silently(unseeded_random_test, cache_dir, watch):
    inspect([unseeded_random_test], Config(), cache_dir=cache_dir)
    for path in cache_dir.iterdir():
        path.write_text('{"not": [an entry')

    findings = inspect([unseeded_random_test], Config(), cache_dir=cache_dir).findings
    written = watch(cache_dir)
    inspect([unseeded_random_test], Config(), cache_dir=cache_dir)

    assert [f.code for f in findings] == ["DS803"]
    assert written() == []


def test_cache_of_the_wrong_shape_is_rebuilt_silently(unseeded_random_test, cache_dir):
    inspect([unseeded_random_test], Config(), cache_dir=cache_dir)
    for path in cache_dir.iterdir():
        path.write_text("[1, 2]")

    findings = inspect([unseeded_random_test], Config(), cache_dir=cache_dir).findings

    assert [f.code for f in findings] == ["DS803"]


def test_cache_off_writes_no_cache(unseeded_random_test, cache_dir):
    inspect([unseeded_random_test], Config(cache=False), cache_dir=cache_dir)

    assert not cache_dir.exists()


def test_unwritable_cache_leaves_the_run_uncached(unseeded_random_test, tmp_path):
    blocked = tmp_path / "blocked"
    blocked.write_text("a file where the cache directory would go")

    findings = inspect([unseeded_random_test], Config(), cache_dir=blocked).findings

    assert [f.code for f in findings] == ["DS803"]


def test_warm_run_reports_at_the_levels_configured_now(assertion_free_test, cache_dir):
    """DS101 is off by default: a cold run with it off, then a warm run with it on."""
    inspect([assertion_free_test], Config(), cache_dir=cache_dir)
    config = Config(levels={"DS101": Level.WARN})

    [finding] = inspect([assertion_free_test], config, cache_dir=cache_dir).findings

    assert finding.level == Level.WARN


def test_warm_run_applies_the_per_file_ignores_configured_now(
    unseeded_random_test, cache_dir
):
    inspect([unseeded_random_test], Config(), cache_dir=cache_dir)
    config = Config(per_file_ignores=(("test_draw.py", frozenset({"DS8"})),))

    assert inspect([unseeded_random_test], config, cache_dir=cache_dir).findings == []


def test_changed_threshold_analyses_files_again(write_test_file, cache_dir):
    path = write_test_file(MOCK_SETUP_OF_THREE)
    inspect([path], Config(max_mock_setup=3, levels=MOCK_SETUP_ON), cache_dir=cache_dir)

    findings = inspect(
        [path], Config(max_mock_setup=2, levels=MOCK_SETUP_ON), cache_dir=cache_dir
    ).findings

    assert [f.code for f in findings] == ["DS303"]


def test_moved_config_root_analyses_files_again(tmp_path, unmarked_test_at, cache_dir):
    """DS901's fix names a directory below the config root."""
    path = unmarked_test_at("integration/test_total.py")
    on = {"DS901": Level.FAIL}
    inspect([path], Config(root=tmp_path, levels=on), cache_dir=cache_dir)

    findings = inspect(
        [path], Config(root=tmp_path / "integration", levels=on), cache_dir=cache_dir
    ).findings

    assert "`@pytest.mark.e2e`" in findings[0].fix
