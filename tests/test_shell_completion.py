from click.testing import CliRunner
from oks_cli.main import cli
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_install_completion_zsh():
    runner = CliRunner()

    result = runner.invoke(cli, ["install-completion", "--type", "zsh"])
    assert result.exit_code == 0
    assert "Autocompletion installed for zsh" in result.output

    completion_file = Path("~/.oks_cli/completions/oks-cli.sh").expanduser()
    assert completion_file.exists()

    script_content = completion_file.read_text()
    assert "compdef _oks_cli_completion oks-cli" in script_content 

def test_install_completion_bash():
    runner = CliRunner()

    result = runner.invoke(cli, ["install-completion", "--type", "bash"])
    assert result.exit_code == 0
    assert "Autocompletion installed for bash" in result.output

    completion_file = Path("~/.oks_cli/completions/oks-cli.sh").expanduser()
    assert completion_file.exists()

    script_content = completion_file.read_text()
    assert "_oks_cli_completion()" in script_content 

def test_bash_completion_suggestions():
    runner = CliRunner()
    env = {
        "_CLI_COMPLETE": "bash_complete",
        "COMP_WORDS": "cli clu",
        "COMP_CWORD": "1",
        "COMP_LINE": "cli clu",
        "COMP_POINT": str(len("cli clu")),
    }
    result = runner.invoke(cli, [], env=env)
    assert "plain,cluster" in result.output

@patch("oks_cli.utils.requests.request")
def test_cluster_dynamic_shell_completion_suggestions(mock_request, add_default_profile):
    def get_env(action: str, flag: str):
        return {
            "_CLI_COMPLETE": "bash_complete",
            "COMP_WORDS": f"cli cluster {action} -p test -c test {flag}",
            "COMP_CWORD": "8",
            "COMP_LINE": f"cli cluster {action} -p test -c test {flag}",
            "COMP_POINT": str(len(f"cli cluster {action} -p test -c test {flag}")),
        }

    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Versions": ["1.33"]})
    ]
    runner = CliRunner()

    result = runner.invoke(cli, [], env=get_env("create", "--version"))
    assert "plain,1.33" in result.output

    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "ControlPlanes": ["cp.3.masters.small", "cp.3.masters.medium"]})
    ]

    result = runner.invoke(cli, [], env=get_env("create", "--control-plane"))
    assert "plain,cp.3.masters.small" in result.output
    assert "plain,cp.3.masters.medium" in result.output

    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "CPSubregions": ["2a", "2b", "2c"]})
    ]

    result = runner.invoke(cli, [], env=get_env("create", '--zone'))
    assert "plain,2a" in result.output
    assert "plain,2b" in result.output
    assert "plain,2c" in result.output


    result = runner.invoke(cli, [], env=get_env("update", "--version"))
    assert "plain,1.33" in result.output

    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "ControlPlanes": ["cp.3.masters.small", "cp.3.masters.medium"]})
    ]

    result = runner.invoke(cli, [], env=get_env("update", "--control-plane"))
    assert "plain,cp.3.masters.small" in result.output
    assert "plain,cp.3.masters.medium" in result.output

def test_profile_dynamic_shell_completion_suggestions(add_default_profile):
    env = {
        "_CLI_COMPLETE": "bash_complete",
        "COMP_WORDS": "cli --profile",
        "COMP_CWORD": "3",
        "COMP_LINE": "cli --profile",
        "COMP_POINT": str(len("cli --profile")),
    }
    runner = CliRunner()

    result = runner.invoke(cli, [], env=env)
    assert "plain,default" in result.output
