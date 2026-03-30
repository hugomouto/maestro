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
