from click.testing import CliRunner
from oks_cli.main import cli
from oks_cli.utils import save_cache
from unittest.mock import patch, MagicMock

def test_cache_clear_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["cache", "clear", "--force"])
    assert result.exit_code == 0

@patch("oks_cli.utils.requests.request")
def test_cache_kubeconfigs_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["--profile", "default", "cache", "kubeconfigs", "-p", "test", "-c", "test"])
    assert result.exit_code == 0
    assert '| user | group | auth | expiration date |' in result.output

# Test "cache kubeconfigs": the cached token kubeconfig is listed as a non expiring token entry
@patch("oks_cli.utils.requests.request")
def test_cache_kubeconfigs_lists_token_kubeconfig(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345"}]})
    ]
    save_cache("12345", "12345", "kubeconfig-token", "kubeconfig", None, None)

    runner = CliRunner()
    result = runner.invoke(cli, ["--profile", "default", "cache", "kubeconfigs", "-p", "test", "-c", "test"])
    assert result.exit_code == 0, result.output
    assert '| -    | -     | token | never           |' in result.output
