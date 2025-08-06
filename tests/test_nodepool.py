from click.testing import CliRunner
from oks_cli.main import cli
from unittest.mock import patch, MagicMock


@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_nodepool_list_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    mock_run.side_effect = [
        MagicMock(returncode = 0, stdout = "Success", stderr = "")
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["cluster", "nodepool", "-p", "test", "-c", "test", "list"])
    mock_run.assert_called()
    
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ["kubectl", "get", "nodepool", "-o", "wide"]

@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_nodepool_create_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {
            "ResponseContext": {},
            "Template": {
                "apiVersion": "oks.dev/v1beta2",
                "kind": "NodePool",
                "metadata": {
                    "name": "NODEPOOL"
                },
                "spec": {
                    "desiredNodes": "NODECOUNT",
                    "nodeType": "NODESIZE",
                    "zones": [],
                    "volumes": []
                }
            }
        }),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    mock_run.side_effect = [
        MagicMock(returncode = 0, stdout = "Success", stderr = "")
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["cluster", "nodepool", "-p", "test", "-c", "test", "create", "-n", "test", "--zone", "eu-west-2a"])

    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert '"apiVersion": "oks.dev/v1beta2"' in kwargs["input"]
    assert '"name": "test"' in kwargs["input"]
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ["kubectl", "create", "-f", "-"]


@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_nodepool_delete_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    mock_run.side_effect = [
        MagicMock(returncode = 0, stdout = "Success", stderr = "")
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["cluster", "nodepool", "-p", "test", "-c", "test", "delete", '-n', 'test'])
    mock_run.assert_called()
    
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ["kubectl", "delete", "nodepool", "test"]
