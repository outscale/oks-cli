from click.testing import CliRunner
from oks_cli.main import cli
from unittest.mock import patch, MagicMock


@patch("oks_cli.utils.requests.request")
def test_cluster_list_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "name": "test"}]}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["cluster", "list", "-p", "test", "-c", "test", '-o', 'json'])
    assert result.exit_code == 0
    assert '"name": "test"' in result.output


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

