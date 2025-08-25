from click.testing import CliRunner
from oks_cli.main import cli


def test_profile_list_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["profile", "list"])
    assert result.exit_code == 0
    assert "There are no profiles" in result.output

def test_profile_list_command_yaml():
    runner = CliRunner()
    result = runner.invoke(cli, ["profile", "list", "--output", "yaml"])
    assert result.exit_code == 0
    assert "There are no profiles" in result.output

def test_profile_list_command_jsonl():
    runner = CliRunner()
    result = runner.invoke(cli, ["profile", "list", "--output", "json"])
    assert result.exit_code == 0
    assert "There are no profiles" in result.output

def test_profile_list_command_wide():
    runner = CliRunner()
    result = runner.invoke(cli, ["profile", "list", "--output", "wide"])
    assert result.exit_code == 0
    assert "There are no profiles" in result.output

def test_profile_list_command_table():
    runner = CliRunner()
    result = runner.invoke(cli, ["profile", "list", "--output", "table"])
    assert result.exit_code == 0
    assert "There are no profiles" in result.output

def test_profile_add_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["profile", "add", "--region", "eu-west-2", "--access-key", "AK", "--secret-key", "SK"])
    assert result.exit_code == 0
    assert "Profile default has been successfully added" in result.output

def test_profile_update_command(add_default_profile):
    runner = CliRunner()
    result = runner.invoke(cli, ["profile", "update", "--profile-name", "default", "--region", "cloudgouv-eu-west-1"])
    assert result.exit_code == 0
    assert "Profile default has been successfully updated" in result.output

def test_profile_update_name_command(add_default_profile):
    """Update a profile changing its name"""
    runner = CliRunner()
    result = runner.invoke(cli, ["profile", "update", "--profile-name", "default", "--new-name", "test", "--force"])
    assert result.exit_code == 0
    assert "Profile default has been successfully updated with new name test" in result.output

def test_profile_delete_command(add_default_profile):
    runner = CliRunner()
    result = runner.invoke(cli, ["profile", "delete", "--profile-name", "default", "--force"])
    assert result.exit_code == 0
    assert "Profile default has been successfully deleted" in result.output