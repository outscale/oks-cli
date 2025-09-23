from click.testing import CliRunner
from oks_cli.main import cli
from unittest.mock import patch, MagicMock

import json 
import yaml

# Test the "cluster list" command: verifies region and profile are shown
@patch("oks_cli.utils.requests.request")
def test_cluster_list_command_with_region_and_profile(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda:
                  {"ResponseContext": {},
                   "Clusters": [
                       {"id": "12345", "name": "test",
                        "statuses": {"status": "ready",
                                     "created_at": "2019-08-24T14:15:22Z",
                                     "updated_at": "2019-08-24T14:15:22Z"}
                        }
                    ]
                  }),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["--profile", "default", "cluster", "list", "-p", "test", "-c", "test"])
    assert result.exit_code == 0
    assert 'eu-west-2' in result.output
    assert 'default' in result.output

# Test the "cluster list" command: verifies listing clusters in a project
@patch("oks_cli.utils.requests.request")
def test_cluster_list_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "name": "test"}]}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["--profile", "default", "cluster", "list", "-p", "test", "-c", "test", '-o', 'json'])
    assert result.exit_code == 0
    assert '"name": "test"' in result.output

# Test the "cluster list" command with all arguments: verifies that advanced filters
@patch("oks_cli.utils.requests.request")
def test_cluster_list_all_args(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "name": "test-cluster"}]}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, [
        "cluster", "list",
        "-p", "test-project",
        "--name", "test-cluster",
        "-c", "test-cluster",
        "--deleted",
        "--plain",
        "--msword",
        "-w",
        "-o", "json",
        "--profile", "default" 
    ])

    assert result.exit_code == 0
    assert "test-cluster" in result.output

# Test the "cluster get" command: verifies fetching details of a specific cluster
@patch("oks_cli.utils.requests.request")
def test_cluster_get_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster": {"id": "12345", "name": "test"}})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["cluster", "get", "-p", "test", "-c", "test"])
    assert result.exit_code == 0
    assert '"name": "test"' in result.output

# Test the "cluster get" command with JSON output: verifies retrieving
@patch("oks_cli.utils.requests.request")
def test_cluster_get_json(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Cluster": {"id": "12345", "name": "test"}}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, [
        "cluster", "get",
        "-p", "test-project",
        "-c", "test",
        "-o", "json",
        "--profile", "default"
    ])

    assert result.exit_code == 0

    data = json.loads(result.output)
    assert "id" in data
    assert "name" in data
    assert data["name"] == "test"

# Test the "cluster get" command with YAML output: verifies retrieving
@patch("oks_cli.utils.requests.request")
def test_cluster_get_yaml(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Cluster": {"id": "12345", "name": "test"}}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, [
        "cluster", "get",
        "-p", "test-project",
        "-c", "test",
        "-o", "yaml",
        "--profile", "default"
    ])

    assert result.exit_code == 0

    data = yaml.safe_load(result.output)
    assert "id" in data
    assert "name" in data
    assert data["name"] == "test"


# Test the "cluster create" command: verifies creating a new cluster in a project
@patch("oks_cli.utils.requests.request")
def test_cluster_create_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Template": {}}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"id": "12345"}}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster": {"id": "12345", "name": "test"}}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["cluster", "create", "-p", "test", "-c", "test"])
    assert result.exit_code == 0
    assert '"name": "test"' in result.output

# Test the "cluster create" command with all arguments: verifies creating a cluster
@patch("oks_cli.utils.requests.request")
@patch("oks_cli.cluster.get_template")
def test_cluster_create_all_args(mock_get_template, mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Template": {}}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Project": {"id": "12345"}}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Cluster": {"id": "12345", "name": "test"}}),
    ]

    mock_get_template.return_value = {}

    runner = CliRunner()
    result = runner.invoke(cli, [
        "cluster", "create",
        "-p", "test-project",
        "-c", "test",
        "--description", "Test cluster",
        "--admin", "10.0.0.1/32",
        "--control-plane", "cp.mono.master",
        "--quirk", "special-feature",
        "--tags", "env=dev",
        "--dry-run",
        "-o", "json",
        "--profile", "default",
    ])

    output = json.loads(result.output)
    assert output["name"] == "test"
    assert output["description"] == "Test cluster"
    assert output["admin_whitelist"] == ["10.0.0.1/32"]
    assert output["control_planes"] == "cp.mono.master"
    assert output["tags"] == {"env": "dev"}
    assert output["quirks"] == ["special-feature"]
    assert output["cp_multi_az"] is False

# Test the "cluster update" command: verifies updating a cluster description (dry-run)
@patch("oks_cli.utils.requests.request")
def test_cluster_update_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["cluster", "update", "-p", "test", "-c", "test", "--description", "test", '--dry-run'])
    assert result.exit_code == 0
    assert '"description": "test"' in result.output

# Test the "cluster update" command with all arguments: verifies updating a cluster
@patch("oks_cli.utils.requests.request")
def test_cluster_update_all_args(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(
            status_code=200, headers={},
            json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}
        ),
        MagicMock(
            status_code=200, headers={},
            json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "name": "test"}]}
        ),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, [
        "cluster", "update",
        "-p", "test-project",
        "-c", "test",
        "--description", "Updated cluster",
        "--admin", "10.0.0.1/32",
        "--control-plane", "cp.mono.master",
        "--quirk", "special-feature",
        "--tags", "env=dev",
        "--dry-run",
        "-o", "json",
        "--profile", "default",
    ])

    output = json.loads(result.output)
    assert output["description"] == "Updated cluster"
    assert output["admin_whitelist"] == ["10.0.0.1/32"]
    assert output["control_planes"] == "cp.mono.master"
    assert output["tags"] == {"env": "dev"}
    assert output["quirks"] == ["special-feature"]

# Test the "cluster upgrade" command: verifies upgrading a cluster
@patch("oks_cli.utils.requests.request")
def test_cluster_upgrade_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster": {"name": "test"}}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["cluster", "upgrade", "-p", "test", "-c", "test", '--force'])
    assert result.exit_code == 0
    assert '"name": "test"' in result.output

# Test the "cluster upgrade" command with JSON output
@patch("oks_cli.utils.requests.request")
def test_cluster_upgrade_command_json(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Cluster": {"name": "test"}}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, [
        "cluster", "upgrade",
        "-p", "test",
        "-c", "test",
        "--force",
        "-o", "json"
    ])
    
    assert result.exit_code == 0

    output = json.loads(result.output)
    assert output["name"] == "test"

# Test the "cluster upgrade" command with YAML output
@patch("oks_cli.utils.requests.request")
def test_cluster_upgrade_command_yaml(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Cluster": {"name": "test"}}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, [
        "cluster", "upgrade",
        "-p", "test",
        "-c", "test",
        "--force",
        "-o", "yaml"
    ])
    
    assert result.exit_code == 0

    output = yaml.safe_load(result.output)
    assert output["name"] == "test"

# Test the "cluster delete" command: verifies dry-run deletion message
@patch("oks_cli.utils.requests.request")
def test_cluster_delete_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["cluster", "delete", "-p", "test", "-c", "test", '--dry-run'])
    assert result.exit_code == 0
    assert 'Dry run: The cluster would be deleted.' in result.output

# Test the "cluster kubeconfig" command: verifies retrieving the kubeconfig of a cluster
@patch("oks_cli.utils.requests.request")
def test_cluster_kubeconfig_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["cluster", "kubeconfig", "-p", "test", "-c", "test"])
    assert result.exit_code == 0
    assert 'kubeconfig' in result.output

# Test the "cluster kubeconfig --output table" command: verifies retrieving the kubeconfig and output as table
@patch("oks_cli.utils.requests.request")
def test_cluster_kubeconfig_info_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["cluster", "kubeconfig", "-p", "test", "-c", "test", "--output", "table"])
    assert result.exit_code != 0
    assert 'Something went wrong, could not parse kubeconfig' in result.output

# Test the "cluster delete" command with JSON output
@patch("oks_cli.utils.requests.request")
def test_cluster_delete_command_json(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Cluster": {"id": "12345", "name": "test"}}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, [
        "cluster", "delete",
        "-p", "test",
        "-c", "test",
        "--force",
        "-o", "json"
    ])

    assert result.exit_code == 0

    output = json.loads(result.output)
    assert output["name"] == "test"

# Test the "cluster delete" command with YAML output
@patch("oks_cli.utils.requests.request")
def test_cluster_delete_command_yaml(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Cluster": {"id": "12345", "name": "test"}}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, [
        "cluster", "delete",
        "-p", "test",
        "-c", "test",
        "--force",
        "-o", "yaml"
    ])

    assert result.exit_code == 0

    output = yaml.safe_load(result.output)
    assert output["name"] == "test"


# Test the "cluster kubectl" command: verifies running kubectl with the cluster's kubeconfig
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_cluster_kubectl_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    mock_run.side_effect = [
        MagicMock(returncode = 0, stdout = "Success", stderr = "")
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["cluster", "-p", "test", "-c", "test", "kubectl", "get", "pods"])
    mock_run.assert_called()

    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ["kubectl", "get", "pods"]

# Test the "cluster create by one-click" command: verifies creating cluster interactively
@patch("oks_cli.utils.os.fork")
@patch("oks_cli.utils.time.sleep")
@patch("oks_cli.utils.requests.request")
def test_cluster_create_by_one_click_command(mock_request,  mock_sleep, mock_fork):

    mock_fork.return_value = 0 

    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": []}),  # GET projects
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Template": {"name": "test"}}),  # get cluster template
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Template": {"name": "test"}}),  # get project template
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"name": "default", "id": "12345"}}), # create new project
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"name": "default", "id": "12345"}]}),  # find_project_id_by_name
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"name": "default", "id": "12345"}]}),  # login into project
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"id": "12345", "status": "pending"}}),  # background wait till ready
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"id": "12345", "status": "ready"}}),  # background
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster": {"id": "cl123", "name": "test"}})
    ]

    runner = CliRunner()
    input_data = "\n".join([
        "y",               # confirm no profile
        "eu-west-2",       # region
        "n",               # use custom endpoint?
        "ak/sk",           # profile type
        "AK",              # AccessKey
        "SK",              # SecretKey
        "y"                # create new project
    ])

    result = runner.invoke(cli, ["cluster", "create",  "-p", "default", "-c", "test"], input=input_data)
    assert result.exit_code == 0

