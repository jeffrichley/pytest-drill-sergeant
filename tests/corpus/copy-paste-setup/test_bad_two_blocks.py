"""Two different setup blocks, each pasted into three tests: one finding each.
Analysed, never run."""

import json

import pytest
from reports import Renderer, Report

pytestmark = pytest.mark.unit


def test_report_renders_its_title(tmp_path):
    path = tmp_path / "data.json"  # expect: DS501
    path.write_text(json.dumps({"title": "Q3"}))
    report = Report.load(path)
    assert Renderer().title(report) == "Q3"


def test_report_renders_no_rows(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(json.dumps({"title": "Q3"}))
    report = Report.load(path)
    assert Renderer().rows(report) == []


def test_report_has_no_footer(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(json.dumps({"title": "Q3"}))
    report = Report.load(path)
    assert Renderer().footer(report) is None


def test_html_renderer_escapes_markup():
    renderer = Renderer(fmt="html")  # expect: DS501
    renderer.theme("plain")
    renderer.escape(True)
    assert renderer.render("<b>") == "&lt;b&gt;"


def test_html_renderer_keeps_text():
    renderer = Renderer(fmt="html")
    renderer.theme("plain")
    renderer.escape(True)
    assert renderer.render("hi").text == "hi"


def test_html_renderer_wraps_lines():
    renderer = Renderer(fmt="html")
    renderer.theme("plain")
    renderer.escape(True)
    assert renderer.render("a\nb").count("<br>") == 1
