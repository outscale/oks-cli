from click.testing import CliRunner
from oks_cli.main import cli
from unittest.mock import patch, MagicMock
import json


@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_list_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]
    fake_response = {
        "apiVersion": "v1",
        "items": [],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }
    mock_run.side_effect = [
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_response).encode("utf-8"), 
            stderr = "")
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "list"])
    mock_run.assert_called()
    
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ['kubectl', 'get', 'netpeerings', '-o', 'json']