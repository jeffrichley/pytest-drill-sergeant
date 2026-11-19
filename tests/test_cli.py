def test_help_names_the_command(cli):
    result = cli("--help")

    assert result.exit_code == 0, result.output
    assert "drill-sergeant" in result.output
