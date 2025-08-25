from click.testing import CliRunner
from oks_cli.main import cli
# from unittest.mock import patch, MagicMock

def test_install_completion_command_type_required():
    """ Test --type option is required """
    runner = CliRunner()
    result = runner.invoke(cli, ["install-completion"])
    assert result.exit_code == 2
    assert "Missing option '--type'" in result.output

def test_install_completion_command_wrong_type():
    """ Test --type supported values """
    runner = CliRunner()
    result = runner.invoke(cli, ["install-completion", "--type", "fake-shell"])
    assert result.exit_code == 2
    assert "Shell completions for fake-shell are not implemented" in result.output

def test_install_completion_command():
    """ Test working shell """
    runner = CliRunner()
    result = runner.invoke(cli, ["install-completion", "--type", "bash"])
    assert result.exit_code == 0
    assert "Autocompletion installed for bash" in result.output