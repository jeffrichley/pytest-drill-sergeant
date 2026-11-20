"""The cache, through the engine seam: per-file results reused while a file's bytes,
drill-sergeant, the config that shapes per-file analysis and the test-tree modules
its analysis followed stay the same."""

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
    """A cold run with DS101 off, then a warm run with it at `fail`."""
    inspect(
        [assertion_free_test], Config(levels={"DS101": Level.OFF}), cache_dir=cache_dir
    )
    config = Config(levels={"DS101": Level.FAIL})

    [finding] = inspect([assertion_free_test], config, cache_dir=cache_dir).findings

    assert finding.level == Level.FAIL


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


# DS101 at `fail`, above its default `warn`, so a finding reads the same either way.
NO_ASSERTION_ON = Config(levels={"DS101": Level.FAIL})
ASSERTING_HELPER = "def check_total(items):\n    assert sum(items) == 3\n"


def test_editing_only_a_followed_helper_module_analyses_the_test_again(
    helper_caller, cache_dir
):
    path, helper = helper_caller
    helper.write_text(ASSERTING_HELPER)
    inspect([path], NO_ASSERTION_ON, cache_dir=cache_dir)
    helper.write_text("def check_total(items):\n    return sum(items)\n")

    findings = inspect([path], NO_ASSERTION_ON, cache_dir=cache_dir).findings

    assert [(f.code, f.line) for f in findings] == [("DS101", 3)]


def test_writing_a_helper_module_that_was_missing_analyses_the_test_again(
    helper_caller, cache_dir
):
    path, helper = helper_caller
    inspect([path], NO_ASSERTION_ON, cache_dir=cache_dir)
    helper.write_text(ASSERTING_HELPER)

    assert inspect([path], NO_ASSERTION_ON, cache_dir=cache_dir).findings == []


def test_warm_run_with_a_followed_helper_unchanged_writes_nothing(
    helper_caller, cache_dir, watch
):
    path, helper = helper_caller
    helper.write_text(ASSERTING_HELPER)
    inspect([path], NO_ASSERTION_ON, cache_dir=cache_dir)
    written = watch(cache_dir)

    inspect([path], NO_ASSERTION_ON, cache_dir=cache_dir)

    assert written() == []


def test_a_project_module_appearing_where_a_third_party_import_was_reanalyses(
    write_test_file, tmp_path, cache_dir
):
    """A call into a third-party package may assert; once the module is the
    project's own, the check sees it asserts nothing."""
    path = write_test_file(
        "from shiplib import ship\n\ndef test_ship():\n    ship(1)\n"
    )
    inspect([path], NO_ASSERTION_ON, cache_dir=cache_dir)
    (tmp_path / "shiplib.py").write_text("def ship(order):\n    return order\n")

    findings = inspect([path], NO_ASSERTION_ON, cache_dir=cache_dir).findings

    assert [(f.code, f.line) for f in findings] == [("DS101", 3)]
