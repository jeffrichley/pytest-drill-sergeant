"""Whole captured output and log text compared with `==`. Analysed, never run."""

import logging

import pytest
from app import cli, greet, main

pytestmark = pytest.mark.unit


def test_greeting_printed(capsys):
    greet("Kenobi")
    assert capsys.readouterr().out == "Hello there, general Kenobi\n"  # expect: DS601


def test_error_printed(capsys):
    main(["--bad"])
    captured = capsys.readouterr()
    assert captured.err == "error: unrecognized arguments: --bad\n"  # expect: DS601


def test_log_line(caplog):
    with caplog.at_level(logging.INFO):
        greet("Ada")
    assert caplog.text == "INFO     app:app.py:12 greeted Ada\n"  # expect: DS601


def test_cli_output(runner):
    result = runner.invoke(cli, ["status"])
    assert result.output == "Status:\n  3 jobs queued\n  0 failed\n"  # expect: DS601


def test_subprocess_stdout(run):
    completed = run(["app", "--version"])
    assert completed.stdout == "app version 1.2.3 (build 42)"  # expect: DS601
