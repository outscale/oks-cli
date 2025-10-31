from click.testing import CliRunner
from oks_cli.main import cli
from unittest.mock import patch, MagicMock
import json
import yaml


# Test the "netpeering" command: verifies it displays help
@patch("oks_cli.utils.requests.request")
def test_netpeering_command(mock_request):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering"])

    assert result.exit_code == 2
    assert "NetPeering related commands" in result.stderr
    assert "create" in result.stderr
    assert "list" in result.stderr
    assert "get" in result.stderr
    assert "delete" in result.stderr

# Test the "netpeering list" command: verifies output is json
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_list_json_command(mock_request, mock_run, add_default_profile):
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

# Test the "netpeering list" command: verifies output is yaml
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_list_yaml_command(mock_request, mock_run, add_default_profile):
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
            stderr = ""),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "list", "-o", "yaml"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    # output format is json by default, then converted into netpeering command output format
    assert args[0] == ['kubectl', 'get', 'netpeerings', '-o', 'json']
    data = yaml.safe_load(result.stdout)
    assert data == fake_response

# Test the "netpeering list -o wide" command: verifies output is wide and empty
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_list_wide_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    mock_run.side_effect = [
        MagicMock(
            returncode = 0,
            stdout = "No resources found".encode("utf-8"),
            stderr = ""),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "list", "-o", "wide"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    # output format is json by default, then converted into netpeering command output format
    assert args[0] == ['kubectl', 'get', 'netpeerings', '-o', 'wide']
    assert "No resources found" in result.stdout

# Test the "netpeering list -o wide" command: verifies output is wide and not empty
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_list_wide_non_empty_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    fake_response  = "NAME                             SOURCE NET ID   ACCEPTER NET ID   NET PEERING ID   STATE NAME   STATE MESSAGE             EXPIRATION DATE\n"
    fake_response += "netpeering.oks.dev/pcx-05a958ce  vpc-3e81fb0e    vpc-7260be2a      pcx-05a958ce     active       Active                    2025-10-23T13:26:29.000Z"
    fake_response += "netpeering.oks.dev/pcx-05a958ce  vpc-3e81fb0e    vpc-7260be2a      pcx-05a958ce     deleted      Deleted by 363338042637   2025-10-23T13:26:29.000Z"

    mock_run.side_effect = [
        MagicMock(
            returncode = 0,
            stdout = fake_response.encode("utf-8"),
            stderr = ""),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "list", "-o", "wide"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    # output format is json by default, then converted into netpeering command output format
    assert args[0] == ['kubectl', 'get', 'netpeerings', '-o', 'wide']
    assert "vpc-3e81fb0e" in result.stdout
    assert "vpc-7260be2a" in result.stdout
    assert "pcx-05a958ce" in result.stdout
    assert "active"       in result.stdout
    assert "deleted"      in result.stdout
    assert "Deleted by 363338042637" in result.stdout

# Test the "netpeering list --status active" command: verifies output is json and only filters active NetPeerings
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_list_status_active_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    fake_response = {
        "apiVersion": "v1",
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        },
        "items": [
            {
                "apiVersion": "oks.dev/v1beta",
                "kind": "NetPeering",
                "metadata": {
                    "annotations": {
                    "kopf.zalando.org/last-handled-configuration": "{\"spec\":{\"netPeeringId\":\"pcx-0ce60092\"}}\n"
                    },
                    "name": "pcx-0ce60092",
                    "resourceVersion": "7908935",
                    "uid": "7d51bb51-05b1-4bcb-af5a-880afa95ef30"
                },
                "spec": {
                    "netPeeringId": "pcx-0ce60092"
                },
                "status": {
                    "accepterIpRange": "10.51.0.0/16",
                    "accepterNetId": "vpc-7260be2a",
                    "accepterOwnerId": "363338042637",
                    "netPeeringExpirationDate": "2025-10-23T09:45:02.000Z",
                    "netPeeringMessage": "Active",
                    "netPeeringState": "active",
                    "sourceIpRange": "10.50.0.0/16",
                    "sourceNetId": "vpc-3e81fb0e",
                    "sourceOwnerId": "374514215886"
                }
            }
        ]
    }

    mock_run.side_effect = [
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_response).encode("utf-8"),
            stderr = ""),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "list", "--status", "active"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    # output format is json by default, then converted into netpeering command output format
    assert args[0] == ['kubectl', 'get', 'netpeerings', '-o', 'json']
    data = json.loads(result.stdout)
    assert data.get('items') != None
    assert len(data.get('items')) == 1
    item = data.get('items')[0]
    assert item.get('kind') == 'NetPeering'
    assert item.get('spec').get('netPeeringId') == 'pcx-0ce60092'
    assert item.get('status').get('netPeeringState') == 'active'
    assert item.get('status').get('accepterNetId') == 'vpc-7260be2a'


# Test the "netpeering list --status deleted" command: verifies output is json and only filters active NetPeerings
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_list_status_deleted_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    fake_response = {
        "apiVersion": "v1",
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        },
        "items": [
            {
                "apiVersion": "oks.dev/v1beta",
                "kind": "NetPeering",
                "metadata": {
                    "annotations": {
                    "kopf.zalando.org/last-handled-configuration": "{\"spec\":{\"netPeeringId\":\"pcx-0ce60092\"}}\n"
                    },
                    "name": "pcx-0ce60092",
                    "resourceVersion": "7908935",
                    "uid": "7d51bb51-05b1-4bcb-af5a-880afa95ef30"
                },
                "spec": {
                    "netPeeringId": "pcx-0ce60092"
                },
                "status": {
                    "accepterIpRange": "10.51.0.0/16",
                    "accepterNetId": "vpc-7260be2a",
                    "accepterOwnerId": "363338042637",
                    "netPeeringExpirationDate": "2025-10-23T09:45:02.000Z",
                    "netPeeringMessage": "Deleted by 363338042637",
                    "netPeeringState": "deleted",
                    "sourceIpRange": "10.50.0.0/16",
                    "sourceNetId": "vpc-3e81fb0e",
                    "sourceOwnerId": "374514215886"
                }
            }
        ]
    }

    mock_run.side_effect = [
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_response).encode("utf-8"),
            stderr = ""),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "list", "--status", "deleted"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    # output format is json by default, then converted into netpeering command output format
    assert args[0] == ['kubectl', 'get', 'netpeerings', '-o', 'json']
    data = json.loads(result.stdout)
    assert data.get('items') != None
    assert len(data.get('items')) == 1
    item = data.get('items')[0]
    assert item.get('kind') == 'NetPeering'
    assert item.get('spec').get('netPeeringId') == 'pcx-0ce60092'
    assert item.get('status').get('netPeeringState') == 'deleted'
    assert item.get('status').get('accepterNetId') == 'vpc-7260be2a'

# Test the "netpeering list --status all" command: verifies output is json and only filters active NetPeerings
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_list_status_all_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    fake_response = {
        "apiVersion": "v1",
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        },
        "items": [
            {
                "apiVersion": "oks.dev/v1beta",
                "kind": "NetPeering",
                "metadata": {
                    "annotations": {
                    "kopf.zalando.org/last-handled-configuration": "{\"spec\":{\"netPeeringId\":\"pcx-0ce60092\"}}\n"
                    },
                    "name": "pcx-0ce60092",
                    "resourceVersion": "7908935",
                    "uid": "7d51bb51-05b1-4bcb-af5a-880afa95ef30"
                },
                "spec": {
                    "netPeeringId": "pcx-0ce60092"
                },
                "status": {
                    "accepterIpRange": "10.51.0.0/16",
                    "accepterNetId": "vpc-7260be2a",
                    "accepterOwnerId": "363338042637",
                    "netPeeringExpirationDate": "2025-10-23T09:45:02.000Z",
                    "netPeeringMessage": "Deleted by 363338042637",
                    "netPeeringState": "deleted",
                    "sourceIpRange": "10.50.0.0/16",
                    "sourceNetId": "vpc-3e81fb0e",
                    "sourceOwnerId": "374514215886"
                }
            }
        ]
    }

    mock_run.side_effect = [
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_response).encode("utf-8"),
            stderr = ""),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "list", "--status", "deleted"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ['kubectl', 'get', 'netpeerings', '-o', 'json']
    data = json.loads(result.stdout)
    assert data.get('items') != None
    assert len(data.get('items')) == 1
    item = data.get('items')[0]
    assert item.get('kind') == 'NetPeering'
    assert item.get('spec').get('netPeeringId') == 'pcx-0ce60092'
    assert item.get('status').get('netPeeringState') == 'deleted'
    assert item.get('status').get('accepterNetId') == 'vpc-7260be2a'

# Test the "netpeering list --status active" command: verifies output is json and using status active filters returns nothing
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_list_status_all_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    fake_response = {
        "apiVersion": "v1",
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        },
        "items": [
            {
                "apiVersion": "oks.dev/v1beta",
                "kind": "NetPeering",
                "metadata": {
                    "name": "pcx-0ce60092",
                },
                "spec": {
                    "netPeeringId": "pcx-0ce60092"
                },
                "status": {
                    "accepterIpRange": "10.51.0.0/16",
                    "accepterNetId": "vpc-7260be2a",
                    "accepterOwnerId": "363338042637",
                    "netPeeringExpirationDate": "2025-10-23T09:45:02.000Z",
                    "netPeeringMessage": "Deleted by 363338042637",
                    "netPeeringState": "deleted",
                    "sourceIpRange": "10.50.0.0/16",
                    "sourceNetId": "vpc-3e81fb0e",
                    "sourceOwnerId": "374514215886"
                }
            }
        ]
    }

    mock_run.side_effect = [
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_response).encode("utf-8"),
            stderr = ""),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "list"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ['kubectl', 'get', 'netpeerings', '-o', 'json']
    data = json.loads(result.stdout)
    assert data.get('items') != None
    assert len(data.get('items')) == 0
    assert data.get('kind') == "List"

# Test the "netpeering delete" command: verifies output is error with message
def test_netpeering_delete_command(add_default_profile):

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "delete"])

    assert result.exit_code == 2
    assert "--project-name must be specified" in result.stderr

# Test the "netpeering delete --dry-run" command: verifies output is error and some option is missing
@patch("oks_cli.utils.requests.request")
def test_netpeering_delete_dryrun_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "delete", "--dry-run"])

    assert result.exit_code == 2
    assert "Missing option '--netpeering-id'" in result.stderr

# Test the "netpeering delete --dry-run --netpeering-id xxxxx" command: verifies dry-run option works as expected
@patch("oks_cli.utils.requests.request")
def test_netpeering_delete_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "delete", "--dry-run", "--netpeering-id", "pcx-4034e83f"])

    assert result.exit_code == 0
    assert "Dry run: The netpeering pcx-4034e83f would be deleted." in result.stdout

# Test the "netpeering delete --netpeering-id xxxxx --force" command: verifies delete option works as expected
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_delete_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    fake_response = "It may take some times for NetPeering pcx-4034e83f to automatically disappear from both projects. Please be patient"

    mock_run.side_effect = [
        MagicMock(
            returncode = 0,
            stdout = fake_response,
            stderr = ""),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "delete", "--netpeering-id", "pcx-4034e83f", "--force"])
    mock_run.assert_called()
    
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ['kubectl', 'delete', 'netpeering', 'pcx-4034e83f']
    assert "NetPeering pcx-4034e83f to automatically disappear" in result.stdout

# Test the "netpeering delete --netpeering-id xxxxx --force" command: verifies delete option fails with the right error message
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_delete_failed_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    mock_run.side_effect = [
        MagicMock(
            returncode = 1,
            stdout = "",
            stderr = "Could not delete NetPeering pcx-4034e83f".encode("utf-8")),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "delete", "--netpeering-id", "pcx-4034e83f", "--force"])
    mock_run.assert_called()
    
    args, kwargs = mock_run.call_args

    assert result.exit_code == 1
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ['kubectl', 'delete', 'netpeering', 'pcx-4034e83f']
    assert "Could not delete NetPeering pcx-4034e83f" in result.stderr

# Test the "netpeering get" command: verifies the command show missing option
@patch("oks_cli.utils.requests.request")
def test_netpeering_get_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "get"])

    assert result.exit_code == 2
    assert "Error: Missing option '--netpeering-id'." in result.stderr

# Test the "netpeering get --netpeering-id pcx-33e30194" command: verifies the command shows output in default json format
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_get_peeringid_json_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    mock_run.side_effect = [
        MagicMock(
            returncode = 0,
            stdout = "OK",
            stderr = ""),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "get", "--netpeering-id", "pcx-33e30194"])
    mock_run.assert_called()
    
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ['kubectl', 'get', 'netpeering', 'pcx-33e30194', '-o', 'json']

# Test the "netpeering get --netpeering-id pcx-33e30194 -o wide" command: verifies the command shows output in wide format
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_get_peeringid_wide_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    mock_run.side_effect = [
        MagicMock(
            returncode = 0,
            stdout = "OK",
            stderr = ""),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "get", "--netpeering-id", "pcx-33e30194", "-o", "wide"])
    mock_run.assert_called()
    
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ['kubectl', 'get', 'netpeering', 'pcx-33e30194', '-o', 'wide']

# Test the "netpeering get --netpeering-id pcx-33e30194 -o wide" command: verifies the command shows output in wide format
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_get_peeringid_yaml_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    mock_run.side_effect = [
        MagicMock(
            returncode = 0,
            stdout = "OK",
            stderr = ""),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "get", "--netpeering-id", "pcx-33e30194", "-o", "yaml"])
    mock_run.assert_called()
    
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ['kubectl', 'get', 'netpeering', 'pcx-33e30194', '-o', 'yaml']


######### CREATE NETPEERING TESTS #############
"""
oks-cli netpeering create --from-project clusterapi --from-cluster clusterapi-management --to-project netpeering --to-cluster netpeering --netpeering-name eqn4 --aut
o-approve
netpeeringrequest.oks.dev/eqn4-989556-npr created
netpeeringacceptance.oks.dev/eqn4-989556-npa created
{
    "apiVersion": "oks.dev/v1beta",
    "kind": "NetPeering",
    "metadata": {
        "annotations": {
            "kopf.zalando.org/last-handled-configuration": "{\"spec\":{\"netPeeringId\":\"pcx-33e30194\"}}\n"
        },
        "creationTimestamp": "2025-10-27T09:02:07Z",
        "finalizers": [
            "kopf.zalando.org/KopfFinalizerMarker"
        ],
        "generation": 1,
        "name": "pcx-33e30194",
        "resourceVersion": "12269072",
        "uid": "eeaf080f-4606-4973-95c4-a4f0a38aab10"
    },
    "spec": {
        "netPeeringId": "pcx-33e30194"
    },
    "status": {
        "accepterIpRange": "10.51.0.0/16",
        "accepterNetId": "vpc-7260be2a",
        "accepterOwnerId": "363338042637",
        "netPeeringExpirationDate": "2025-11-03T09:02:07.000Z",
        "netPeeringMessage": "Active",
        "netPeeringState": "active",
        "sourceIpRange": "10.50.0.0/16",
        "sourceNetId": "vpc-3e81fb0e",
        "sourceOwnerId": "374514215886"
    }
}
NetPeering pcx-33e30194 successfully created and active between projects 'clusterapi' and 'netpeering'
"""

# Test the "netpeering create" command: verifies an error is thrown about overlaping networks
# netpeering create --from-project projectA --from-cluster clusterA \
#                   --to-project projectB --to-cluster clusterB     \
#                   --netpeering-name testC --auto-approve

@patch("oks_cli.utils.requests.request")
def test_netpeering_create_netoverlap_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        # Before netpeering subcommand
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),

        # Project A
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "cidr": "10.50.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        # Project B
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "67890", "cidr": "10.50.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "67890"}]}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "projectA", "-c", "clusterA",
                                 "create", "--netpeering-name", "test", "--auto-approve",
                                 "--from-project", "projectA", "--from-cluster", "clusterA",
                                 "--to-project", "projectB", "--to-cluster", "clusterB"])
    assert result.exit_code == 1
    assert "Error: Source network 10.50.0.0/16 and target network 10.50.0.0/16 overlap, you can't create netpeering. Aborted!\n" in result.stderr

# Test the "netpeering create" command: verifies that a NetPeering already exists
# netpeering create --from-project projectA --from-cluster clusterA \
#                   --to-project projectA --to-cluster clusterA     \
#                   --netpeering-name testC

@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_create_peering_exists_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        # Before netpeering subcommand
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),

        # Project A - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectA", "cidr": "10.50.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "name": "clusterA"}]}),
        # Project B - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectB", "cidr": "10.51.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "name": "clusterB"}]}),

        # clusterA - get nodepool
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # clusterB - get nodepool
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # _netpeering_exists - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    fake_nodepoolA = {
        "apiVersion": "v1",
        "items": [
            {
                "apiVersion": "oks.dev/v1beta2",
                "kind": "NodePool",
                "metadata": {
                    "labels": {
                        "oks.account-id": "374514215886",
                        "oks.network_id": "vpc-3e81fb0e",
                        "oks.nodepool.security-group": "sg-fe577828"
                    },
                    "name": "NodepoolA",
                },
                "spec": {
                    "zones": [
                        "eu-west-2c"
                    ]
                },
            },
        ],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    fake_nodepoolB = {
        "apiVersion": "v1",
        "items": [
            {
                "apiVersion": "oks.dev/v1beta2",
                "kind": "NodePool",
                "metadata": {
                    "labels": {
                        "oks.account-id": "363338042637",
                        "oks.network_id": "vpc-7260be2a",
                        "oks.nodepool.security-group": "sg-fe577829"
                    },
                    "name": "NodepoolB",
                },
                "spec": {
                    "zones": [
                        "eu-west-2c"
                    ]
                },
            },
        ],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    fake_netpeering = {
        "apiVersion": "v1",
        "items": [
            {
                "apiVersion": "oks.dev/v1beta",
                "kind": "NetPeering",
                "metadata": {
                    "name": "pcx-33e30194",
                },
                "spec": {
                    "netPeeringId": "pcx-33e30194"
                },
                "status": {
                    "accepterIpRange": "10.51.0.0/16",
                    "accepterNetId": "vpc-7260be2a",
                    "accepterOwnerId": "363338042637",
                    "netPeeringMessage": "Active",
                    "netPeeringState": "active",
                    "sourceIpRange": "10.50.0.0/16",
                    "sourceNetId": "vpc-3e81fb0e",
                    "sourceOwnerId": "374514215886"
                }
            }
        ],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    fake_response = "already exists between projects projectA and projectB. Aborting!"
    mock_run.side_effect = [
        # get source nodepool
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_nodepoolA).encode("utf-8"),
            stderr = "",
        ),
        # get target nodepool
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_nodepoolB).encode("utf-8"),
            stderr = "",
        ),
        # check existing netpeering
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_netpeering).encode("utf-8"),
            stderr = "",
        ),
    ]
    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "projectA", "-c", "clusterA",
                                 "create", "--netpeering-name", "test",
                                 "--from-project", "projectA", "--from-cluster", "clusterA",
                                 "--to-project", "projectB", "--to-cluster", "clusterB"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args
    assert result.exit_code == 1
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ['kubectl', 'get', 'netpeering', '-o', 'json']
    assert fake_response in result.output

# Test the "netpeering create" command: verifies that a NetPeering already exists
# netpeering create --from-project projectA --from-cluster clusterA \
#                   --to-project projectA --to-cluster clusterA     \
#                   --netpeering-name testC --dry-run

@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_create_dryrun_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        # Before netpeering subcommand
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),

        # Project A - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectA", "cidr": "10.50.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "name": "clusterA"}]}),
        # Project B - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "67890", "name": "projectB", "cidr": "10.51.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "67890", "name": "clusterB"}]}),

        # clusterA - get nodepool
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # clusterB - get nodepool
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # _netpeering_exists - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    fake_nodepoolA = {
        "apiVersion": "v1",
        "items": [
            {
                "apiVersion": "oks.dev/v1beta2",
                "kind": "NodePool",
                "metadata": {
                    "labels": {
                        "oks.account-id": "374514215886",
                        "oks.network_id": "vpc-3e81fb0e",
                        "oks.nodepool.security-group": "sg-fe577828"
                    },
                    "name": "NodepoolA",
                },
                "spec": {
                    "zones": [
                        "eu-west-2c"
                    ]
                },
            },
        ],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    fake_nodepoolB = {
        "apiVersion": "v1",
        "items": [
            {
                "apiVersion": "oks.dev/v1beta2",
                "kind": "NodePool",
                "metadata": {
                    "labels": {
                        "oks.account-id": "363338042637",
                        "oks.network_id": "vpc-7260be2a",
                        "oks.nodepool.security-group": "sg-fe577829"
                    },
                    "name": "NodepoolB",
                },
                "spec": {
                    "zones": [
                        "eu-west-2c"
                    ]
                },
            },
        ],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    fake_netpeering_exists = {
        "apiVersion": "v1",
        "items": [],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    mock_run.side_effect = [
        # get source nodepool
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_nodepoolA).encode("utf-8"),
            stderr = "",
        ),
        # get target nodepool
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_nodepoolB).encode("utf-8"),
            stderr = "",
        ),
        # check existing netpeering
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_netpeering_exists).encode("utf-8"),
            stderr = "",
        ),
    ]
    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "projectA", "-c", "clusterA",
                                 "create", "--netpeering-name", "mynetpeering-name",
                                 "--from-project", "projectA", "--from-cluster", "clusterA",
                                 "--to-project", "projectB", "--to-cluster", "clusterB", "--dry-run"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args
    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ['kubectl', 'get', 'netpeering', '-o', 'json']
    data = json.loads(result.output)
    assert data.get("kind") == "NetPeeringRequest"
    assert "mynetpeering-name" in data.get("metadata").get("name")
    assert data.get("spec").get('accepterNetId') == "vpc-7260be2a"
    assert data.get("spec").get('accepterOwnerId') == "363338042637"

# Test the "netpeering create" command: verifies that a NetPeering fails because of an error during apply
# netpeering create --from-project projectA --from-cluster clusterA \
#                   --to-project projectA --to-cluster clusterA     \
#                   --netpeering-name testC

@patch("time.sleep")
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_create_requestexception_command(mock_request, mock_run, mock_sleep, add_default_profile):
    mock_request.side_effect = [
        # Before netpeering subcommand
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),

        # Project A - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectA", "cidr": "10.50.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "name": "clusterA"}]}),
        # Project B - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "67890", "name": "projectB", "cidr": "10.51.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "67890", "name": "clusterB"}]}),

        # clusterA - get nodepool
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # clusterB - get nodepool
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # _netpeering_exists - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # create netpeering request - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # create get netpeeringrequests - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    fake_nodepoolA = {
        "apiVersion": "v1",
        "items": [
            {
                "apiVersion": "oks.dev/v1beta2",
                "kind": "NodePool",
                "metadata": {
                    "labels": {
                        "oks.account-id": "374514215886",
                        "oks.network_id": "vpc-3e81fb0e",
                        "oks.nodepool.security-group": "sg-fe577828"
                    },
                    "name": "NodepoolA",
                },
                "spec": {
                    "zones": [
                        "eu-west-2c"
                    ]
                },
            },
        ],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    fake_nodepoolB = {
        "apiVersion": "v1",
        "items": [
            {
                "apiVersion": "oks.dev/v1beta2",
                "kind": "NodePool",
                "metadata": {
                    "labels": {
                        "oks.account-id": "363338042637",
                        "oks.network_id": "vpc-7260be2a",
                        "oks.nodepool.security-group": "sg-fe577829"
                    },
                    "name": "NodepoolB",
                },
                "spec": {
                    "zones": [
                        "eu-west-2c"
                    ]
                },
            },
        ],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    fake_netpeering_exists = {
        "apiVersion": "v1",
        "items": [],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    fake_netpeeringrequests = "Error from server (NotFound): netpeerings.oks.dev \"test\" not found"

    mock_run.side_effect = [
        # get source nodepool
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_nodepoolA).encode("utf-8"),
            stderr = "",
        ),
        # get target nodepool
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_nodepoolB).encode("utf-8"),
            stderr = "",
        ),
        # check existing netpeering
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_netpeering_exists).encode("utf-8"),
            stderr = "",
        ),
        # create netpeering request - kubectl create -f -
        MagicMock(
            returncode = 0,
            stdout = "created",
            stderr = ""
        ),
        # # get netpeeringrequests id
        MagicMock(
            returncode = 1,
            stdout = json.dumps(fake_netpeeringrequests).encode("utf-8"),
            stderr = ""
        ),
    ]
    mock_sleep.return_value = None
    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "projectA", "-c", "clusterA",
                                 "create", "--netpeering-name", "mynetpeering-name",
                                 "--from-project", "projectA", "--from-cluster", "clusterA",
                                 "--to-project", "projectB", "--to-cluster", "clusterB"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args
    assert result.exit_code == 1
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert "kubectl get netpeeringrequests -o json mynetpeering-name" in " ".join(args[0])
    assert "Cannot create NetPeeringRequest:" in result.stderr

# Test the "netpeering create" command: verifies that a NetPeering state is in wrong state
# netpeering create --from-project projectA --from-cluster clusterA \
#                   --to-project projectA --to-cluster clusterA     \
#                   --netpeering-name testC

@patch("time.sleep")
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_create_netpeering_wrongstate_command(mock_request, mock_run, mock_sleep, add_default_profile):
    mock_request.side_effect = [
        # Before netpeering subcommand
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),

        # Project A - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectA", "cidr": "10.50.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "name": "clusterA"}]}),
        # Project B - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "67890", "name": "projectB", "cidr": "10.51.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "67890", "name": "clusterB"}]}),

        # clusterA - get nodepool
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # clusterB - get nodepool
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # _netpeering_exists - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # create netpeering request - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        #  get netpeeringrequests - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    fake_nodepoolA = {
        "apiVersion": "v1",
        "items": [
            {
                "apiVersion": "oks.dev/v1beta2",
                "kind": "NodePool",
                "metadata": {
                    "labels": {
                        "oks.account-id": "374514215886",
                        "oks.network_id": "vpc-3e81fb0e",
                        "oks.nodepool.security-group": "sg-fe577828"
                    },
                    "name": "NodepoolA",
                },
                "spec": {
                    "zones": [
                        "eu-west-2c"
                    ]
                },
            },
        ],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    fake_nodepoolB = {
        "apiVersion": "v1",
        "items": [
            {
                "apiVersion": "oks.dev/v1beta2",
                "kind": "NodePool",
                "metadata": {
                    "labels": {
                        "oks.account-id": "363338042637",
                        "oks.network_id": "vpc-7260be2a",
                        "oks.nodepool.security-group": "sg-fe577829"
                    },
                    "name": "NodepoolB",
                },
                "spec": {
                    "zones": [
                        "eu-west-2c"
                    ]
                },
            },
        ],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    fake_netpeering_exists = {
        "apiVersion": "v1",
        "kind": "NetPeeringRequest",
        "metadata": {
            "resourceVersion": ""
        },
        "items": []
    }

    fake_netpeering_requests = {
        "apiVersion": "v1",
        "kind": "NetPeeringRequest",
        "metadata": {
            "resourceVersion": ""
        },
        "status": {
            "netPeeringState": "wrong-state",
            "netPeeringId": "pcx-33e30194"
        }
    }

    mock_run.side_effect = [
        # get source nodepool
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_nodepoolA).encode("utf-8"),
            stderr = "",
        ),
        # get target nodepool
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_nodepoolB).encode("utf-8"),
            stderr = "",
        ),
        # check existing netpeering
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_netpeering_exists).encode("utf-8"),
            stderr = "",
        ),
        # create netpeering request - kubectl create -f -
        MagicMock(
            returncode = 0,
            stdout = "created",
            stderr = ""
        ),
        # # get netpeering_requests id
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_netpeering_requests).encode("utf-8"),
            stderr = ""
        ),
    ]
    mock_sleep.return_value = None
    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "projectA", "-c", "clusterA",
                                 "create", "--netpeering-name", "mynetpeering-name",
                                 "--from-project", "projectA", "--from-cluster", "clusterA",
                                 "--to-project", "projectB", "--to-cluster", "clusterB"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args
    assert result.exit_code == 1
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert "kubectl get netpeeringrequests -o json mynetpeering-name" in " ".join(args[0])
    assert "NetPeeringAcceptance is in wrong state: wrong-state" in result.stderr

# Test the "netpeering create" command: verifies that a NetPeeringAcceptance fails
# netpeering create --from-project projectA --from-cluster clusterA \
#                   --to-project projectA --to-cluster clusterA     \
#                   --netpeering-name testC

@patch("time.sleep")
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_create_netpeeringacceptance_fails_command(mock_request, mock_run, mock_sleep, add_default_profile):
    mock_request.side_effect = [
        # Before netpeering subcommand
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),

        # Project A - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectA", "cidr": "10.50.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "name": "clusterA"}]}),
        # Project B - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "67890", "name": "projectB", "cidr": "10.51.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "67890", "name": "clusterB"}]}),

        # clusterA - get nodepool
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # clusterB - get nodepool
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # _netpeering_exists - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # create netpeering request - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get netpeeringrequests - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # create netpeering acceptance - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
    ]

    fake_nodepoolA = {
        "apiVersion": "v1",
        "items": [
            {
                "apiVersion": "oks.dev/v1beta2",
                "kind": "NodePool",
                "metadata": {
                    "labels": {
                        "oks.account-id": "374514215886",
                        "oks.network_id": "vpc-3e81fb0e",
                        "oks.nodepool.security-group": "sg-fe577828"
                    },
                    "name": "NodepoolA",
                },
                "spec": {
                    "zones": [
                        "eu-west-2c"
                    ]
                },
            },
        ],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    fake_nodepoolB = {
        "apiVersion": "v1",
        "items": [
            {
                "apiVersion": "oks.dev/v1beta2",
                "kind": "NodePool",
                "metadata": {
                    "labels": {
                        "oks.account-id": "363338042637",
                        "oks.network_id": "vpc-7260be2a",
                        "oks.nodepool.security-group": "sg-fe577829"
                    },
                    "name": "NodepoolB",
                },
                "spec": {
                    "zones": [
                        "eu-west-2c"
                    ]
                },
            },
        ],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    fake_netpeering_exists = {
        "apiVersion": "v1",
        "kind": "NetPeeringRequest",
        "metadata": {
            "resourceVersion": ""
        },
        "items": []
    }

    fake_netpeering_requests = {
        "apiVersion": "v1",
        "kind": "NetPeeringRequest",
        "metadata": {
            "resourceVersion": ""
        },
        "status": {
            "netPeeringState": "pending-acceptance",
            "netPeeringId": "pcx-33e30194"
        }
    }

    mock_run.side_effect = [
        # get source nodepool
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_nodepoolA).encode("utf-8"),
            stderr = "",
        ),
        # get target nodepool
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_nodepoolB).encode("utf-8"),
            stderr = "",
        ),
        # check existing netpeering
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_netpeering_exists).encode("utf-8"),
            stderr = "",
        ),
        # create netpeering request - kubectl create -f -
        MagicMock(
            returncode = 0,
            stdout = "created",
            stderr = ""
        ),
        # get netpeering_requests id
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_netpeering_requests).encode("utf-8"),
            stderr = ""
        ),
        # create netpeeringacceptance - kubectl create -f -
        MagicMock(
            returncode = 1,
            stdout = "",
            stderr = ""
        )
    ]
    mock_sleep.return_value = None
    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "projectA", "-c", "clusterA",
                                 "create", "--netpeering-name", "mynetpeering-name", "--auto-approve",
                                 "--from-project", "projectA", "--from-cluster", "clusterA",
                                 "--to-project", "projectB", "--to-cluster", "clusterB"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args
    assert result.exit_code == 1
    assert ".oks_cli/cache/67890-67890/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert "kubectl create -f -" in " ".join(args[0])
    assert "Error: Could not create NetPeeringAcceptance object" in result.stderr

# Test the "netpeering create" command: verifies that a NetPeering just created has a wrong-state
# netpeering create --from-project projectA --from-cluster clusterA \
#                   --to-project projectA --to-cluster clusterA     \
#                   --netpeering-name testC

@patch("time.sleep")
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_create_netpeering_checkstate_ok_command(mock_request, mock_run, mock_sleep, add_default_profile):
    mock_request.side_effect = [
        # Before netpeering subcommand
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),

        # Project A - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectA", "cidr": "10.50.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "name": "clusterA"}]}),
        # Project B - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "67890", "name": "projectB", "cidr": "10.51.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "67890", "name": "clusterB"}]}),

        # clusterA - get nodepool
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # clusterB - get nodepool
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # _netpeering_exists - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # create netpeering request - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get netpeeringrequests - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # create netpeering acceptance - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get netpeering acceptance (wait for status) - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get netpeering acceptance (wait for status) - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get netpeering acceptance (wait for status) - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
    ]

    fake_nodepoolA = {
        "apiVersion": "v1",
        "items": [
            {
                "apiVersion": "oks.dev/v1beta2",
                "kind": "NodePool",
                "metadata": {
                    "labels": {
                        "oks.account-id": "374514215886",
                        "oks.network_id": "vpc-3e81fb0e",
                        "oks.nodepool.security-group": "sg-fe577828"
                    },
                    "name": "NodepoolA",
                },
                "spec": {
                    "zones": [
                        "eu-west-2c"
                    ]
                },
            },
        ],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    fake_nodepoolB = {
        "apiVersion": "v1",
        "items": [
            {
                "apiVersion": "oks.dev/v1beta2",
                "kind": "NodePool",
                "metadata": {
                    "labels": {
                        "oks.account-id": "363338042637",
                        "oks.network_id": "vpc-7260be2a",
                        "oks.nodepool.security-group": "sg-fe577829"
                    },
                    "name": "NodepoolB",
                },
                "spec": {
                    "zones": [
                        "eu-west-2c"
                    ]
                },
            },
        ],
        "kind": "List",
        "metadata": {
            "resourceVersion": ""
        }
    }

    fake_netpeering_exists = {
        "apiVersion": "v1",
        "kind": "NetPeeringRequest",
        "metadata": {
            "resourceVersion": ""
        },
        "items": []
    }

    fake_netpeering_requests = {
        "apiVersion": "v1",
        "kind": "NetPeeringRequest",
        "metadata": {
            "resourceVersion": ""
        },
        "status": {
            "netPeeringState": "pending-acceptance",
            "netPeeringId": "pcx-33e30194"
        }
    }

    fake_get_first_netpeering = {
        "apiVersion": "v1",
        "kind": "NetPeering",
        "metadata": {
            "resourceVersion": ""
        },
        "status": {
            "netPeeringState": "pending-acceptance",
            "netPeeringId": "pcx-33e30194"
        }
    }

    fake_get_second_netpeering = {
        "apiVersion": "v1",
        "kind": "NetPeering",
        "metadata": {
            "resourceVersion": ""
        },
        "status": {
            "netPeeringState": "pending-acceptance",
            "netPeeringId": "pcx-33e30194"
        }
    }

    fake_get_third_netpeering = {
        "apiVersion": "v1",
        "kind": "NetPeering",
        "metadata": {
            "resourceVersion": ""
        },
        "status": {
            "netPeeringState": "active",
            "netPeeringId": "pcx-33e30194"
        }
    }

    mock_run.side_effect = [
        # get source nodepool
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_nodepoolA).encode("utf-8"),
            stderr = "",
        ),
        # get target nodepool
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_nodepoolB).encode("utf-8"),
            stderr = "",
        ),
        # check existing netpeering
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_netpeering_exists).encode("utf-8"),
            stderr = "",
        ),
        # create netpeering request - kubectl create -f -
        MagicMock(
            returncode = 0,
            stdout = "created",
            stderr = ""
        ),
        # get netpeering_requests id
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_netpeering_requests).encode("utf-8"),
            stderr = ""
        ),
        # create netpeeringacceptance - kubectl create -f -
        MagicMock(
            returncode = 0,
            stdout = "",
            stderr = ""
        ),
        # get netpeering - get netpeering -o json
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_get_first_netpeering).encode("utf-8"),
            stderr = ""
        ),
        # get netpeering - get netpeering -o json
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_get_second_netpeering).encode("utf-8"),
            stderr = ""
        ),
        # get netpeering - get netpeering -o json
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_get_third_netpeering).encode("utf-8"),
            stderr = ""
        )
    ]
    # mock_sleep.return_value = None
    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "projectA", "-c", "clusterA",
                                 "create", "--netpeering-name", "mynetpeering-name", "--auto-approve",
                                 "--from-project", "projectA", "--from-cluster", "clusterA",
                                 "--to-project", "projectB", "--to-cluster", "clusterB"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args
    assert result.exit_code == 0
    assert ".oks_cli/cache/67890-67890/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert ['kubectl', 'get', 'netpeering', '-o', 'json', 'pcx-33e30194'] == args[0]
    assert "NetPeering pcx-33e30194 successfully created and active between projects 'projectA' and 'projectB'\n" in result.stdout


# Test the "netpeering create" command: verifies that a when --auto-approve is not set, the netpeering request is deleted
# netpeering create --from-project projectA --from-cluster clusterA \
#                   --to-project projectA --to-cluster clusterA     \
#                   --netpeering-name testC

# @patch("time.sleep")
# @patch("oks_cli.utils.subprocess.run")
# @patch("oks_cli.utils.requests.request")
# def test_netpeering_create_netpeering_delete_due_to_abort_command(mock_request, mock_run, mock_sleep, add_default_profile):
#     mock_request.side_effect = [
#         # Before netpeering subcommand
#         MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
#         MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),

#         # Project A - gather_info
#         MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectA", "cidr": "10.50.0.0/16"}]}),
#         MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "name": "clusterA"}]}),
#         # Project B - gather_info
#         MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "67890", "name": "projectB", "cidr": "10.51.0.0/16"}]}),
#         MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "67890", "name": "clusterB"}]}),

#         # clusterA - get nodepool
#         MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
#         # clusterB - get nodepool
#         MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
#         # check is a netpeering already exists - _run_kubectl
#         MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
#         # create netpeering request - _run_kubectl - create -f -
#         MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
#         # get netpeeringrequests - _run_kubectl - kubectl get netpeeringrequests
#         MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
#         # delete netpeeringrequests - _run_kubectl
#         MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),

#     ]

#     fake_nodepoolA = {
#         "apiVersion": "v1",
#         "items": [
#             {
#                 "apiVersion": "oks.dev/v1beta2",
#                 "kind": "NodePool",
#                 "metadata": {
#                     "labels": {
#                         "oks.account-id": "374514215886",
#                         "oks.network_id": "vpc-3e81fb0e",
#                         "oks.nodepool.security-group": "sg-fe577828"
#                     },
#                     "name": "NodepoolA",
#                 },
#                 "spec": {
#                     "zones": [
#                         "eu-west-2c"
#                     ]
#                 },
#             },
#         ],
#         "kind": "List",
#         "metadata": {
#             "resourceVersion": ""
#         }
#     }

#     fake_nodepoolB = {
#         "apiVersion": "v1",
#         "items": [
#             {
#                 "apiVersion": "oks.dev/v1beta2",
#                 "kind": "NodePool",
#                 "metadata": {
#                     "labels": {
#                         "oks.account-id": "363338042637",
#                         "oks.network_id": "vpc-7260be2a",
#                         "oks.nodepool.security-group": "sg-fe577829"
#                     },
#                     "name": "NodepoolB",
#                 },
#                 "spec": {
#                     "zones": [
#                         "eu-west-2c"
#                     ]
#                 },
#             },
#         ],
#         "kind": "List",
#         "metadata": {
#             "resourceVersion": ""
#         }
#     }

#     fake_netpeering_exists = {
#         "apiVersion": "v1",
#         "kind": "NetPeeringRequest",
#         "metadata": {
#             "resourceVersion": ""
#         },
#         "items": []
#     }

#     fake_netpeering_requests = {
#         "apiVersion": "v1",
#         "kind": "NetPeeringRequest",
#         "metadata": {
#             "resourceVersion": ""
#         },
#         "status": {
#             "netPeeringState": "pending-acceptance",
#             "netPeeringId": "pcx-33e30194"
#         }
#     }


#     mock_run.side_effect = [
#         # get source nodepool
#         MagicMock(
#             returncode = 0,
#             stdout = json.dumps(fake_nodepoolA).encode("utf-8"),
#             stderr = "",
#         ),
#         # get target nodepool
#         MagicMock(
#             returncode = 0,
#             stdout = json.dumps(fake_nodepoolB).encode("utf-8"),
#             stderr = "",
#         ),
#         # check existing netpeering
#         MagicMock(
#             returncode = 0,
#             stdout = json.dumps(fake_netpeering_exists).encode("utf-8"),
#             stderr = "",
#         ),
#         # create netpeering request - kubectl create -f -
#         MagicMock(
#             returncode = 0,
#             stdout = "created",
#             stderr = ""
#         ),
#         # get netpeering_requests id
#         MagicMock(
#             returncode = 0,
#             stdout = json.dumps(fake_netpeering_requests).encode("utf-8"),
#             stderr = ""
#         ),
#         # delete netpeering requests due to no auto-approve
#         MagicMock(
#             returncode = 0,
#             stdout = "",
#             stderr = ""
#         )
#     ]
#     # mock_sleep.return_value = None
#     runner = CliRunner()
#     result = runner.invoke(cli, ["netpeering", "-p", "projectA", "-c", "clusterA",
#                                  "create", "--netpeering-name", "mynetpeering-name",
#                                  "--from-project", "projectA", "--from-cluster", "clusterA",
#                                  "--to-project", "projectB", "--to-cluster", "clusterB"])
#     mock_run.assert_called()
#     args, kwargs = mock_run.call_args
#     assert result.exit_code == 0
#     assert ".oks_cli/cache/67890-67890/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
#     assert "kubectl delete netpeeringrequests" in " ".join(args[0])
#     assert "deleted due to abort.\n" in result.stdout
