from click.testing import CliRunner
from oks_cli.main import cli
from unittest.mock import patch, MagicMock

import yaml


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
    result = runner.invoke(cli, ["cluster", "nodepool", "-p", "test", "-c", "test", "delete", '-n', 'test', '--force'])
    mock_run.assert_called()
    
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ["kubectl", "delete", "nodepool", "test"]

@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_nodepool_list_auth_token_command(mock_request, mock_run, add_default_profile):
    issued = yaml.safe_dump({
        "clusters": [{"name": "test", "cluster": {"server": "https://kube.example:6443", "certificate-authority-data": "Q0E="}}],
    })
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": issued}}})
    ]
    mock_run.return_value = MagicMock(returncode = 0, stdout = "Success", stderr = "")

    runner = CliRunner()
    result = runner.invoke(cli, ["cluster", "nodepool", "-p", "test", "-c", "test", "--auth", "token", "list"])
    assert result.exit_code == 0, result.output

    assert mock_request.call_args.kwargs["params"] == {"ttl": "1s"}
    args, kwargs = mock_run.call_args
    assert kwargs["env"]["KUBECONFIG"].endswith(".oks_cli/cache/12345-12345/default/default/kubeconfig-token")
    assert args[0] == ["kubectl", "get", "nodepool", "-o", "wide"]

@patch("oks_cli.utils.requests.request")
def test_nodepool_auth_token_rejects_user_group(mock_request, add_default_profile):
    runner = CliRunner()
    result = runner.invoke(cli, ["cluster", "nodepool", "-p", "test", "-c", "test", "--auth", "token", "--user", "admin", "list"])
    assert result.exit_code != 0
    assert "only supported with --auth cert" in result.output
    mock_request.assert_not_called()
