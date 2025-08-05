from click.testing import CliRunner
from oks_cli.main import cli
from unittest.mock import patch, MagicMock

@patch("oks_cli.utils.requests.request")
def test_quotas_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda:  {"ResponseContext": {}, "Quotas": []})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["quotas"])
    
    assert result.exit_code == 0
    assert "[]" in result.output

@patch("oks_cli.utils.requests.request")
def test_quotas_command_table(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda:  {"ResponseContext": {}, "Quotas": []})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["quotas", "-o", "table"])
    
    assert result.exit_code == 0
    assert "| Projects | Clusters per project | Kubernetes versions" in result.output
