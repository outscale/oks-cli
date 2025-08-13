from click.testing import CliRunner
from oks_cli.main import cli
from pathlib import Path


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
