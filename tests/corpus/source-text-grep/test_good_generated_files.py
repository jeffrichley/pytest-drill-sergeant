"""Near-misses: `.py` files the test writes or the code under test generates, and
text that was never read from a file. Analysed, never run."""

from app import generate_stub, run_tool

SNIPPET = "def handler():\n    return 1\n"


def test_tool_reports_the_written_file(tmp_path):
    (tmp_path / "plugin.py").write_text(SNIPPET)
    result = run_tool(tmp_path / "plugin.py")
    assert "plugin.py" in result.output


def test_snippet_defines_a_handler():
    assert "def handler" in SNIPPET


def test_stub_written_with_a_signature(tmp_path):
    generate_stub("handler", tmp_path / "handler.py")
    assert "def handler(" in (tmp_path / "handler.py").read_text()
