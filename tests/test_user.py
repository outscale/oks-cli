from click.testing import CliRunner
from oks_cli.main import cli
from unittest.mock import patch, MagicMock

@patch("oks_cli.utils.requests.request")
def test_user_list_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "EimUsers":  []})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["user", "list", "-p", "test"])
    assert result.exit_code == 0
    assert 'USER | ACCESS KEY' in result.output

@patch("oks_cli.utils.requests.request")
def test_user_create_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "EimUser":  {
            "UserName": "OKSAuditor",
            "CreationDate": "2026-03-04T12:31:58.000+0000",
            "UserId": "BlaBla",
            "UserEmail": "bla@email.local",
            "LastModificationDate": "2026-03-04T12:31:58.000+0000",
            "Path": "/",
            "AccessKeys": [
            {
                "State": "ACTIVE",
                "AccessKeyId": "AK",
                "CreationDate": "2026-03-04T12:31:59.841+0000",
                "ExpirationDate": "2026-03-11T12:31:59.297+0000",
                "SecretKey": "SK",
                "LastModificationDate": "2026-03-04T12:31:59.841+0000"
            }
            ]
        }})
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["user", "create", "-p", "test", "-u", "OKSAuditor", "--ttl", "1w"])
    assert result.exit_code == 0
    assert 'bla@email.local' in result.output

@patch("oks_cli.utils.requests.request")
def test_user_delete_command(mock_request, add_default_profile):
    mock_request.side_effect = [
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers = {}, json=lambda: {"ResponseContext": {}, "Details": "User has been deleted." })
    ]

    runner = CliRunner()
    result = runner.invoke(cli, ["user", "delete", "-p", "test", "-u", "OKSAuditor", "--force"])
    assert result.exit_code == 0
    assert 'User has been deleted.' in result.output