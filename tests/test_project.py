from click.testing import CliRunner
from oks_cli.main import cli
from unittest.mock import patch, MagicMock


@patch("oks_cli.utils.requests.request")
def test_project_list_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "list", '-o', 'json'])
    assert result.exit_code == 0
    assert '"id": "12345' in result.output


@patch("oks_cli.utils.requests.request")
def test_project_get_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"id": "12345"}})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "get", '-p', 'test'])
    assert result.exit_code == 0
    assert '"id": "12345"' in result.output


@patch("oks_cli.utils.requests.request")
def test_project_create_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Template": {}})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "create", '-p', 'test', '--dry-run'])
    assert result.exit_code == 0
    assert '"name": "test"' in result.output


@patch("oks_cli.utils.requests.request")
def test_project_update_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "update", '-p', 'test', '--description', 'test', '--dry-run'])
    assert result.exit_code == 0
    assert '"description": "test"' in result.output

@patch("oks_cli.utils.requests.request")
def test_project_delete_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "delete", '-p', 'test', '--dry-run', '--force'])
    assert result.exit_code == 0
    assert 'Dry run: The project would be deleted.' in result.output


@patch("oks_cli.utils.requests.request")
def test_project_quotas_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Quotas": {"data": []}})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "quotas", "-p", "test"])
    assert result.exit_code == 0
    assert '[]' in result.output


@patch("oks_cli.utils.requests.request")
def test_project_snapshots_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Snapshots": []})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "snapshots", "-p", "test"])
    assert result.exit_code == 0
    assert '[]' in result.output


@patch("oks_cli.utils.requests.request")
def test_project_publicips_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "PublicIps": []})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "publicips", "-p", "test"])
    assert result.exit_code == 0
    assert '[]' in result.output