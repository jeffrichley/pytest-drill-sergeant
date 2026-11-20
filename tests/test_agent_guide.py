from importlib.metadata import version

import pytest

from pytest_drill_sergeant.checks import CHECKS

pytestmark = pytest.mark.integration

START = "<!-- drill-sergeant agent guide"
END = "<!-- /drill-sergeant agent guide -->"


@pytest.mark.parametrize("check", CHECKS, ids=lambda c: c.code)
def test_agent_guide_teaches_each_check_from_the_registry(cli, check):
    result = cli("agent-guide")

    assert result.exit_code == 0, result.output
    assert check.why in result.output
    assert check.bad_example in result.output
    assert check.good_example in result.output


def test_agent_guide_states_the_waiver_rule(cli):
    output = cli("agent-guide").output

    assert "explicit yes" in output


@pytest.mark.parametrize(
    ("existing", "target", "skill"),
    [
        ((), "AGENTS.md", ".agents/skills/drill-sergeant/SKILL.md"),
        (("AGENTS.md",), "AGENTS.md", ".agents/skills/drill-sergeant/SKILL.md"),
        (("CLAUDE.md",), "CLAUDE.md", ".claude/skills/drill-sergeant/SKILL.md"),
        (
            ("AGENTS.md", "CLAUDE.md"),
            "AGENTS.md",
            ".agents/skills/drill-sergeant/SKILL.md",
        ),
    ],
    ids=["neither", "AGENTS.md", "CLAUDE.md", "both"],
)
def test_install_writes_the_skill_and_a_block_in_agents_md_or_claude_md(
    cli, tmp_path, existing, target, skill
):
    for name in existing:
        (tmp_path / name).write_text("# Notes\n")

    result = cli("agent-guide", "--install")

    assert result.exit_code == 0, result.output
    assert START in (tmp_path / target).read_text()
    assert (tmp_path / skill).is_file()
    assert sorted(p.name for p in tmp_path.glob("*.md")) == sorted({*existing, target})


def test_install_leaves_claude_md_alone_beside_agents_md(cli, tmp_path):
    (tmp_path / "AGENTS.md").write_text("# Agents\n")
    (tmp_path / "CLAUDE.md").write_text("# Claude\n")

    cli("agent-guide", "--install")

    assert (tmp_path / "CLAUDE.md").read_text() == "# Claude\n"


def test_install_marks_the_block_with_the_version(cli, tmp_path):
    cli("agent-guide", "--install")

    first = (tmp_path / "AGENTS.md").read_text().splitlines()[0]
    assert first.startswith(START)
    assert version("pytest-drill-sergeant") in first


def test_installed_block_points_at_the_skill_and_explain(cli, tmp_path):
    cli("agent-guide", "--install")

    block = (tmp_path / "AGENTS.md").read_text()
    assert ".agents/skills/drill-sergeant/SKILL.md" in block
    assert "drill-sergeant explain" in block


def test_installed_block_states_the_waiver_rule(cli, tmp_path):
    cli("agent-guide", "--install")

    assert "explicit yes" in (tmp_path / "AGENTS.md").read_text()


def test_installed_skill_names_itself_and_holds_the_full_guide(cli, tmp_path):
    guide = cli("agent-guide").output

    cli("agent-guide", "--install")

    skill = (tmp_path / ".agents/skills/drill-sergeant/SKILL.md").read_text()
    assert skill.startswith("---\nname: drill-sergeant\ndescription: ")
    assert guide in skill


def test_reinstall_replaces_only_the_block(cli, tmp_path):
    (tmp_path / "CLAUDE.md").write_text(
        f"# Before\n\n{START} v0.0.1 -->\nstale guide\n{END}\n\n# After\n"
    )

    cli("agent-guide", "--install")

    text = (tmp_path / "CLAUDE.md").read_text()
    assert text.startswith(f"# Before\n\n{START} v{version('pytest-drill-sergeant')}")
    assert text.endswith(f"{END}\n\n# After\n")
    assert "stale guide" not in text
    assert text.count(START) == 1


def test_reinstall_is_idempotent(cli, tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Claude\n")
    cli("agent-guide", "--install")
    first = {p: p.read_text() for p in tmp_path.rglob("*") if p.is_file()}

    cli("agent-guide", "--install")

    assert {p: p.read_text() for p in tmp_path.rglob("*") if p.is_file()} == first


def test_install_refuses_a_block_with_no_end(cli, tmp_path):
    (tmp_path / "AGENTS.md").write_text(f"{START} v0.0.1 -->\nstale guide\n")

    assert cli("agent-guide", "--install").exit_code == 2
