def test_plugin_is_active_once_installed(pytester):
    pytester.makepyfile(
        """
        def test_registered(request):
            assert request.config.pluginmanager.hasplugin("drill_sergeant")
        """
    )

    result = pytester.runpytest("-p", "no:randomly")

    result.assert_outcomes(passed=1)


def test_plugin_leaves_a_passing_run_passing(pytester):
    pytester.makepyfile("def test_ok():\n    assert 1 + 1 == 2\n")

    result = pytester.runpytest("-p", "no:randomly")

    assert result.ret == 0
