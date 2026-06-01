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

# Test the "netpeering list" command: verifies output is table
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_list_table_command(mock_request, mock_run, add_default_profile):
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
    assert args[0] == ['kubectl', 'get', 'netpeerings']

# Test the "netpeering list" command: verifies output is yaml
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_list_yaml_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

    mock_run.side_effect = [
        MagicMock(
            returncode = 0,
            stdout = "", 
            stderr = ""),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "list", "-o", "yaml"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ['kubectl', 'get', 'netpeerings', '-o', 'yaml']

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
            stdout = "",
            stderr = ""),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "-p", "test", "-c", "test", "list", "-o", "wide"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args

    assert result.exit_code == 0
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]

    assert args[0] == ['kubectl', 'get', 'netpeerings', '-o', 'wide']

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

# Test the "netpeering create" command: verifies an error is thrown about overlaping networks
@patch("oks_cli.utils.requests.request")
def test_netpeering_create_netoverlap_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        # Project A
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "cidr": "10.50.0.0/16", "name": "projectA"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "project_id": "12345", "name": "clusterA"}]}),
        # Project B
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "67890", "cidr": "10.50.0.0/16", "name": "projectB"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "67890", "project_id": "67890", "name": "clusterB"}]}),
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "create", "--netpeering-name", "test",
                                 "--source-project", "projectA", "--source-cluster", "clusterA",
                                 "--target-project", "projectB", "--target-cluster", "clusterB"])
    assert result.exit_code == 1
    assert "Error: Source network 10.50.0.0/16 and target network 10.50.0.0/16 overlap, you can't create netpeering. Aborted!\n" in result.stderr

# Test the "netpeering create" command: verifies that a NetPeering already exists
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_create_peering_exists_command(mock_request, mock_run, add_default_profile):
    mock_request.side_effect = [

        # Project A - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectA", "cidr": "10.50.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "project_id": "12345", "name": "clusterA"}]}),
        # Project B - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectB", "cidr": "10.51.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "project_id": "12345", "name": "clusterB"}]}),

        
        # GET vpc and account id for Project A
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Nets": [{"IpRange": "10.50.0.0/16", "NetId": "vpc-3e81fb0e"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"data": { "quotas": [{ "AccountId": "374514215886"}]}}}),

        # GET vpc and account id for Project B
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Nets": [{"IpRange": "10.51.0.0/16", "NetId": "vpc-7260be2a"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"data": { "quotas": [{ "AccountId": "363338042637"}]}}}),

        # _netpeering_exists - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}})
    ]

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
        MagicMock(
            returncode = 0,
            stdout = json.dumps(fake_netpeering).encode("utf-8"),
            stderr = "",
        ),
    ]
    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "create", "--netpeering-name", "test", "--force",
                                 "--source-project", "projectA", "--source-cluster", "clusterA",
                                 "--target-project", "projectB", "--target-cluster", "clusterB"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args
    assert result.exit_code == 1
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert args[0] == ['kubectl', 'get', 'netpeering', '-o', 'json']
    assert fake_response in result.output

# Test the "netpeering create" command: verifies dry run
@patch("oks_cli.utils.requests.request")
def test_netpeering_create_dryrun_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        # Project A - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectA", "cidr": "10.50.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "project_id": "12345", "name": "clusterA"}]}),
        # Project B - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectB", "cidr": "10.51.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "project_id": "12345", "name": "clusterB"}]}),
        # get NetPeeringRequest template
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Template": {
                "apiVersion": "oks.dev/v1beta",
                "kind": "NetPeeringRequest",
                "metadata": {
                    "name": "NAME"
                },
                "spec": {
                    "accepterNetId": "NETID",
                    "accepterOwnerId": "OWNERID"
                }
            }
        }),
        # get NetPeeringAcceptance template
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Template": {
                "apiVersion": "oks.dev/v1beta",
                "kind": "NetPeeringAcceptance",
                "metadata": {
                    "name": "NAME"
                },
                "spec": {
                    "netPeeringId": "NETID"
                }
            }
        })
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "create", "--netpeering-name", "mynetpeering-name", "--dry-run",
                                 "--source-project", "projectA", "--source-cluster", "clusterA",
                                 "--target-project", "projectB", "--target-cluster", "clusterB"])
    assert result.exit_code == 0
    data = json.loads(result.output)

    assert data[0].get("kind") == "NetPeeringRequest"
    assert data[1].get("kind") == "NetPeeringAcceptance"
    assert "mynetpeering-name" in data[0].get("metadata").get("name")
    assert "mynetpeering-name" in data[1].get("metadata").get("name")

# Test the "netpeering create" command: verifies that a NetPeering fails because of an error during apply
@patch("time.sleep")
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_create_requestexception_command(mock_request, mock_run, mock_sleep, add_default_profile):
    mock_request.side_effect = [
        # Project A - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectA", "cidr": "10.50.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "project_id": "12345", "name": "clusterA"}]}),

        # Project B - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "67890", "name": "projectB", "cidr": "10.51.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "67890", "project_id": "67890", "name": "clusterB"}]}),

        # GET vpc and account id for Project A
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Nets": [{"IpRange": "10.50.0.0/16", "NetId": "vpc-3e81fb0e"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"data": { "quotas": [{ "AccountId": "374514215886"}]}}}),

        # GET vpc and account id for Project B
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Nets": [{"IpRange": "10.51.0.0/16", "NetId": "vpc-7260be2a"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"data": { "quotas": [{ "AccountId": "363338042637"}]}}}),

        # _netpeering_exists - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get NetPeeringRequest template
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Template": {
                "apiVersion": "oks.dev/v1beta",
                "kind": "NetPeeringRequest",
                "metadata": {
                    "name": "NAME"
                },
                "spec": {
                    "accepterNetId": "NETID",
                    "accepterOwnerId": "OWNERID"
                }
            }
        }),
        # create netpeering request - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get netpeeringrequests - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
    ]

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
    result = runner.invoke(cli, ["netpeering", "create", "--netpeering-name", "mynetpeering-name", "--force",
                                 "--source-project", "projectA", "--source-cluster", "clusterA",
                                 "--target-project", "projectB", "--target-cluster", "clusterB"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args
    assert result.exit_code == 1
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert "kubectl get netpeeringrequests -o json mynetpeering-name" in " ".join(args[0])
    assert "Cannot create NetPeeringRequest:" in result.stderr

# Test the "netpeering create" command: verifies that a NetPeering state is in wrong state
@patch("time.sleep")
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_create_netpeering_wrongstate_command(mock_request, mock_run, mock_sleep, add_default_profile):
    mock_request.side_effect = [
        # Project A - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectA", "cidr": "10.50.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "project_id": "12345", "name": "clusterA"}]}),

        # Project B - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "67890", "name": "projectB", "cidr": "10.51.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "67890", "project_id": "67890", "name": "clusterB"}]}),

        # GET vpc and account id for Project A
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Nets": [{"IpRange": "10.50.0.0/16", "NetId": "vpc-3e81fb0e"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"data": { "quotas": [{ "AccountId": "374514215886"}]}}}),

        # GET vpc and account id for Project B
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Nets": [{"IpRange": "10.51.0.0/16", "NetId": "vpc-7260be2a"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"data": { "quotas": [{ "AccountId": "363338042637"}]}}}),

        # _netpeering_exists - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get NetPeeringRequest template
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Template": {
                "apiVersion": "oks.dev/v1beta",
                "kind": "NetPeeringRequest",
                "metadata": {
                    "name": "NAME"
                },
                "spec": {
                    "accepterNetId": "NETID",
                    "accepterOwnerId": "OWNERID"
                }
            }
        }),
        # create netpeering request - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get netpeeringrequests - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get NetPeeringAcceptance template
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Template": {
                "apiVersion": "oks.dev/v1beta",
                "kind": "NetPeeringAcceptance",
                "metadata": {
                    "name": "NAME"
                },
                "spec": {
                    "netPeeringId": "NETID"
                }
            }
        }),
        # create netpeering acceptance - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
    ]

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
    result = runner.invoke(cli, ["netpeering", "create", "--netpeering-name", "mynetpeering-name", "--force",
                                 "--source-project", "projectA", "--source-cluster", "clusterA",
                                 "--target-project", "projectB", "--target-cluster", "clusterB"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args
    assert result.exit_code == 1
    assert ".oks_cli/cache/12345-12345/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert "kubectl get netpeeringrequests -o json mynetpeering-name" in " ".join(args[0])
    assert "NetPeeringAcceptance is in wrong state: wrong-state" in result.stderr

# Test the "netpeering create" command: verifies that a NetPeeringAcceptance fails
@patch("time.sleep")
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_create_netpeeringacceptance_fails_command(mock_request, mock_run, mock_sleep, add_default_profile):
    mock_request.side_effect = [
        # Project A - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectA", "cidr": "10.50.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "project_id": "12345", "name": "clusterA"}]}),

        # Project B - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "67890", "name": "projectB", "cidr": "10.51.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "67890", "project_id": "67890", "name": "clusterB"}]}),

        # GET vpc and account id for Project A
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Nets": [{"IpRange": "10.50.0.0/16", "NetId": "vpc-3e81fb0e"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"data": { "quotas": [{ "AccountId": "374514215886"}]}}}),

        # GET vpc and account id for Project B
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Nets": [{"IpRange": "10.51.0.0/16", "NetId": "vpc-7260be2a"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"data": { "quotas": [{ "AccountId": "363338042637"}]}}}),

        # _netpeering_exists - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get NetPeeringRequest template
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Template": {
                "apiVersion": "oks.dev/v1beta",
                "kind": "NetPeeringRequest",
                "metadata": {
                    "name": "NAME"
                },
                "spec": {
                    "accepterNetId": "NETID",
                    "accepterOwnerId": "OWNERID"
                }
            }
        }),
        # create netpeering request - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get netpeeringrequests - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get NetPeeringAcceptance template
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Template": {
                "apiVersion": "oks.dev/v1beta",
                "kind": "NetPeeringAcceptance",
                "metadata": {
                    "name": "NAME"
                },
                "spec": {
                    "netPeeringId": "NETID"
                }
            }
        }),
        # create netpeering acceptance - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
    ]

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
    result = runner.invoke(cli, ["netpeering", "create", "--netpeering-name", "mynetpeering-name", "--force",
                                 "--source-project", "projectA", "--source-cluster", "clusterA",
                                 "--target-project", "projectB", "--target-cluster", "clusterB"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args
    assert result.exit_code == 1
    assert ".oks_cli/cache/67890-67890/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert "kubectl create -f -" in " ".join(args[0])
    assert "Error: Could not create NetPeeringAcceptance object" in result.stderr

# Test the "netpeering create" command: verifies that a NetPeering just created has a wrong-state
@patch("time.sleep")
@patch("oks_cli.utils.subprocess.run")
@patch("oks_cli.utils.requests.request")
def test_netpeering_create_netpeering_checkstate_ok_command(mock_request, mock_run, mock_sleep, add_default_profile):
    mock_request.side_effect = [
        # Project A - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345", "name": "projectA", "cidr": "10.50.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "project_id": "12345", "name": "clusterA"}]}),

        # Project B - gather_info
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "67890", "name": "projectB", "cidr": "10.51.0.0/16"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "67890", "project_id": "67890", "name": "clusterB"}]}),

        # GET vpc and account id for Project A
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Nets": [{"IpRange": "10.50.0.0/16", "NetId": "vpc-3e81fb0e"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"data": { "quotas": [{ "AccountId": "374514215886"}]}}}),

        # GET vpc and account id for Project B
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Nets": [{"IpRange": "10.51.0.0/16", "NetId": "vpc-7260be2a"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Project": {"data": { "quotas": [{ "AccountId": "363338042637"}]}}}),

        # _netpeering_exists - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get NetPeeringRequest template
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Template": {
                "apiVersion": "oks.dev/v1beta",
                "kind": "NetPeeringRequest",
                "metadata": {
                    "name": "NAME"
                },
                "spec": {
                    "accepterNetId": "NETID",
                    "accepterOwnerId": "OWNERID"
                }
            }
        }),
        # create netpeering request - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get netpeeringrequests - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
        # get NetPeeringAcceptance template
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Template": {
                "apiVersion": "oks.dev/v1beta",
                "kind": "NetPeeringAcceptance",
                "metadata": {
                    "name": "NAME"
                },
                "spec": {
                    "netPeeringId": "NETID"
                }
            }
        }),
        # create netpeering acceptance - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),

        # get netpeering (wait for status) - _run_kubectl
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Cluster":  {"data": {"kubeconfig": "kubeconfig"}}}),
    ]

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

    mock_run.side_effect = [
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
        )
    ]
    mock_sleep.return_value = None
    runner = CliRunner()
    result = runner.invoke(cli, ["netpeering", "create", "--netpeering-name", "mynetpeering-name", "--force",
                                 "--source-project", "projectA", "--source-cluster", "clusterA",
                                 "--target-project", "projectB", "--target-cluster", "clusterB"])
    mock_run.assert_called()
    args, kwargs = mock_run.call_args
    assert result.exit_code == 0
    assert ".oks_cli/cache/67890-67890/default/default/kubeconfig" in kwargs["env"]["KUBECONFIG"]
    assert ['kubectl', 'get', 'netpeering', '-o', 'json', 'pcx-33e30194'] == args[0]