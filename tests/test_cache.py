from click.testing import CliRunner
from oks_cli.main import cli
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
    assert '| user | group | expiration date |' in result.output