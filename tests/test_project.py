from click.testing import CliRunner
from oks_cli.main import cli
from unittest.mock import patch, MagicMock
import yaml
import json 

# START PROJECT LIST COMMAND
# Test the "project list" command: verifies region and profile are shown
@patch("oks_cli.utils.requests.request")
def test_project_list_command_with_region_and_profile(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {
            "ResponseContext": {},
            "Projects": [
                {"id": "12345",
                 "name":"test",
                 "created_at": "2019-08-24T14:15:22Z",
                 "updated_at": "2019-08-24T14:15:22Z",
                 "status": "ready",
                 "region":"eu-west-2"}]})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "list"])
    assert result.exit_code == 0
    assert 'eu-west-2' in result.output
    assert 'default' in result.output

# Test the "project list" command: verifies listing 1 projects with json
@patch("oks_cli.utils.requests.request")
def test_project_list_command_json(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "list", '-o', 'json'])
    assert result.exit_code == 0
    assert '"id": "12345' in result.output

# Test the "project list" command: verifies listing 1 projects with yaml
@patch("oks_cli.utils.requests.request")
def test_project_list_command_yaml(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "list", '-o', 'yaml'])
    assert result.exit_code == 0
    data = yaml.safe_load(result.output)
    assert data[0]["id"] == "12345"

# Test the "project list" command: verifies listing multiples projects with json
@patch("oks_cli.utils.requests.request")
def test_project_list_multiple_projects_json(mock_request):
    mock_request.return_value = MagicMock(
        status_code=200,
        headers={},
        json=lambda: {
            "ResponseContext": {},
            "Projects": [
                {"id": "12345"},
                {"id": "67890"},
            ]
        },
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "list", "-o", "json"])

    assert result.exit_code == 0
    assert '"id": "12345"' in result.output
    assert '"id": "67890"' in result.output

# Test the "project list" command: verifies listing multiples projects with yaml
@patch("oks_cli.utils.requests.request")
def test_project_list_multiple_projects_yaml(mock_request):
    mock_request.return_value = MagicMock(
        status_code=200,
        headers={},
        json=lambda: {
            "ResponseContext": {},
            "Projects": [
                {"id": "12345"},
                {"id": "67890"},
            ]
        },
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "list", "-o", "yaml"])

    assert result.exit_code == 0
    data = yaml.safe_load(result.output)
    assert data[0]["id"] == "12345"
    assert data[1]["id"] == "67890"
# END PROJECT LIST COMMAND

# START PROJECT GET COMMAND
# Test the "project get" command: verifies fetching a specific project's details
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

# Test the "project get" command: verifies fetching a specific project's details with output json
@patch("oks_cli.utils.requests.request")
def test_project_get_command_output_json(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]})
    ]

    runner = CliRunner()

    result_json = runner.invoke(cli, ["project", "get", "-p", "test", "--output", "json"])
    assert result_json.exit_code == 0
    assert '"id": "12345"' in result_json.output

# Test the "project get" command: verifies fetching a specific project's details with output yaml
@patch("oks_cli.utils.requests.request")
def test_project_get_command_output_yaml(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]})
    ]

    runner = CliRunner()

    result_yaml = runner.invoke(cli, ["project", "get", "-p", "test", "--output", "yaml"])
    data = yaml.safe_load(result_yaml.output)
    assert data[0]["id"] == "12345"
# END PROJECT GET COMMAND

# START PROJECT CREATE COMMAND
# Test the "project create" command: verifies dry-run project creation
@patch("oks_cli.utils.requests.request")
def test_project_create_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Template": {}})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "create", '-p', 'test', '--dry-run'])
    assert result.exit_code == 0
    assert '"name": "test"' in result.output

# Test the "project create" command: verifies all args for project creation
@patch("oks_cli.utils.requests.request")
def test_project_create_all_args(mock_request):
    mock_request.return_value = MagicMock(
        status_code=200,
        headers={},
        json=lambda: {"ResponseContext": {}, "Template": {}}
    )

    runner = CliRunner()
    result = runner.invoke(cli, [
        "project", "create",
        "-p", "test-project",
        "--description", "This is a test project",
        "--cidr", "10.0.0.0/16",
        "--quirk", "some-quirk",
        "--tags", "env=dev,team=qa",
        "--disable-api-termination", "true",
        "--dry-run",
        "-o", "json",
        "--profile", "default"
    ])

    assert result.exit_code == 0

    data = json.loads(result.output)

    assert data["name"] == "test-project"
    assert data["description"] == "This is a test project"
    assert data["cidr"] == "10.0.0.0/16"
    assert data["quirks"] == ["some-quirk"]
    assert data["tags"] == {"env": "dev", "team": "qa"}
    assert data["disable_api_termination"] is True
# END PROJECT CREATE COMMAND

# START PROJECT UPDATE COMMAND

# START PROJECT UPDATE COMMAND
# Test the "project update" command: verifies updating project description in dry-run mode
@patch("oks_cli.utils.requests.request")
def test_project_update_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "update", '-p', 'test', '--description', 'test', '--dry-run'])
    assert result.exit_code == 0
    assert '"description": "test"' in result.output

# Test the "project update" command: verifies all args for project update
@patch("oks_cli.utils.requests.request")
def test_project_update_all_args(mock_request, add_default_profile):
    mock_request.return_value = MagicMock(
        status_code=200,
        headers={},
        json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}
    )

    runner = CliRunner()
    result = runner.invoke(cli, [
        "project", "update",
        "-p", "test-project",
        "--description", "Updated project description",
        "--quirk", "new-quirk",
        "--tags", "env=prod,team=ops",
        "--disable-api-termination", "false",
        "--dry-run",
        "-o", "json",
        "--profile", "default"
    ])

    assert result.exit_code == 0

    data = json.loads(result.output)

    assert data["description"] == "Updated project description"
    assert data["quirks"] == ["new-quirk"]
    assert data["tags"] == {"env": "prod", "team": "ops"}
    assert data["disable_api_termination"] is False
# END PROJECT UPDATE COMMAND

# START PROJECT DELETE COMMAND
# Test the "project delete" command: verifies dry-run deletion message
@patch("oks_cli.utils.requests.request")
def test_project_delete_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["project", "delete", '-p', 'test', '--dry-run', '--force'])
    assert result.exit_code == 0
    assert 'Dry run: The project would be deleted.' in result.output

# Test the "project delete" command with JSON output: verifies dry-run deletion message is valid JSON
@patch("oks_cli.utils.requests.request")
def test_project_delete_json(mock_request, add_default_profile):
    # Simuler la réponse de l'API
    mock_request.return_value = MagicMock(
        status_code=200,
        headers={},
        json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}
    )

    runner = CliRunner()
    result = runner.invoke(cli, [
        "project", "delete",
        "-p", "test-project",
        "--dry-run",
        "--force",
        "-o", "json",
        "--profile", "default"
    ])

    assert result.exit_code == 0

    # La sortie doit être du JSON valide
    data = json.loads(result.output)
    assert "message" in data
    assert data["message"] == "Dry run: The project would be deleted."

# Test the "project delete" command with YAML output: verifies dry-run deletion message is valid YAML
@patch("oks_cli.utils.requests.request")
def test_project_delete_yaml(mock_request, add_default_profile):
    # Simuler la réponse de l'API
    mock_request.return_value = MagicMock(
        status_code=200,
        headers={},
        json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}
    )

    runner = CliRunner()
    result = runner.invoke(cli, [
        "project", "delete",
        "-p", "test-project",
        "--dry-run",
        "--force",
        "-o", "yaml",
        "--profile", "default"
    ])

    assert result.exit_code == 0

    # La sortie doit être du YAML valide
    data = yaml.safe_load(result.output)
    assert "message" in data
    assert data["message"] == "Dry run: The project would be deleted."
# END PROJECT DELETE COMMAND

# START PROJECT QUOTAS COMMAND
# Test the "project quotas" command: verifies fetching project quotas
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
def test_project_quotas_json(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Quotas": {"data": []}})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, [
        "project", "quotas",
        "-p", "test-project",
        "-o", "json",
        "--profile", "default"
    ])

    assert result.exit_code == 0

    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data == []


@patch("oks_cli.utils.requests.request")
def test_project_quotas_yaml(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Quotas": {"data": []}})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, [
        "project", "quotas",
        "-p", "test-project",
        "-o", "yaml",
        "--profile", "default"
    ])

    assert result.exit_code == 0

    data = yaml.safe_load(result.output)
    assert isinstance(data, list)
    assert data == []
# END PROJECT DELETE COMMAND

# START PROJECT SNAPSHOT COMMAND
# Test the "project snapshots" command: verifies fetching project snapshots
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
def test_project_snapshots_json(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Snapshots": []})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, [
        "project", "snapshots",
        "-p", "test-project",
        "-o", "json",
        "--profile", "default"
    ])

    assert result.exit_code == 0

    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data == []

@patch("oks_cli.utils.requests.request")
def test_project_snapshots_yaml(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Snapshots": []})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, [
        "project", "snapshots",
        "-p", "test-project",
        "-o", "yaml",
        "--profile", "default"
    ])

    assert result.exit_code == 0

    data = yaml.safe_load(result.output)
    assert isinstance(data, list)
    assert data == []
# END PROJECT SNAPSHOT COMMAND

# START PROJECT PUBLICIPS COMMAND
# Test the "project publicips" command: verifies fetching project public IPs
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

@patch("oks_cli.utils.requests.request")
def test_project_publicips_json(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "PublicIps": []})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, [
        "project", "publicips",
        "-p", "test-project",
        "-o", "json",
        "--profile", "default"
    ])

    assert result.exit_code == 0

    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data == []

@patch("oks_cli.utils.requests.request")
def test_project_publicips_yaml(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "PublicIps": []})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, [
        "project", "publicips",
        "-p", "test-project",
        "-o", "yaml",
        "--profile", "default"
    ])

    assert result.exit_code == 0

    data = yaml.safe_load(result.output)
    assert isinstance(data, list)
    assert data == []
# END PROJECT PUBLICIPS COMMAND