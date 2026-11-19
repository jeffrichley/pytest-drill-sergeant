def test_help_exits_zero_and_names_the_command(cli):
    result = cli("--help")

    assert result.exit_code == 0, result.output
    assert "drill-sergeant" in result.output


def test_no_arguments_shows_usage(cli):
    result = cli()

    assert "Usage" in result.output
