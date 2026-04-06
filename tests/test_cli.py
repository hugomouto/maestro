from click.testing import CliRunner
from maestro.cli import main


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["version"])
    assert result.exit_code == 0
    assert "Maestro" in result.output


def test_skills_lists_build_team():
    runner = CliRunner()
    result = runner.invoke(main, ["skills"])
    assert result.exit_code == 0
    assert "MAESTRO-build-team" in result.output


def test_skills_shows_description():
    runner = CliRunner()
    result = runner.invoke(main, ["skills"])
    assert "Elicita" in result.output


def test_claude_md_exists():
    from pathlib import Path
    assert Path("CLAUDE.md").exists(), "CLAUDE.md deve existir na raiz"


def test_claude_md_has_skill():
    from pathlib import Path
    content = Path("CLAUDE.md").read_text()
    assert "/MAESTRO-build-team" in content, "CLAUDE.md deve conter a skill"


def test_claude_md_has_framework_block():
    from pathlib import Path
    content = Path("CLAUDE.md").read_text()
    assert "<!-- MAESTRO:framework -->" in content
    assert "<!-- /MAESTRO:framework -->" in content
