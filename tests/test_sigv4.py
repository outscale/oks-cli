from click.testing import CliRunner
from oks_cli.main import cli
from oks_cli.utils import build_signed_requests_token, encode_signed_requests_token, \
                          decode_signed_requests_token, get_sigv4_token_file, save_sigv4_token
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

import json
import os
import pytest
import requests


CLUSTER_LIST = ["--profile", "default", "cluster", "list", "-p", "test", "-c", "test", "-o", "json"]


@pytest.fixture(autouse=True)
def clean_sigv4_env(monkeypatch):
    # the CLI exports OKS_PROFILE to os.environ, make sure it does not leak between tests
    monkeypatch.delenv("OKS_PROFILE", raising=False)
    monkeypatch.setenv("OKS_RETRIES", "1")


def run_token():
    result = CliRunner().invoke(cli, ["--profile", "default", "cluster", "token"])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def clusters_responses():
    return [
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Projects": [{"id": "12345"}]}),
        MagicMock(status_code=200, headers={}, json=lambda: {"ResponseContext": {}, "Clusters": [{"id": "12345", "name": "test"}]}),
    ]


def rejected_response():
    response = MagicMock(status_code=401, headers={}, text='{"message": "Unauthorized: Invalid SigV4 token."}')
    response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=response)
    return response


def record_authorizations(mock_request, responses):
    """Answer with `responses` and record the Authorization header at the time of each call."""
    sent = []
    responses = iter(responses)

    def request(method, url, *args, **kwargs):
        # do_request retries reuse and mutate the same headers dict
        sent.append(kwargs["headers"]["Authorization"])
        return next(responses)

    mock_request.side_effect = request
    return sent


# Test "cluster token": the token is not cached and expires at AmzDate + 14 minutes
def test_cluster_token_is_not_cached(add_default_profile, monkeypatch):
    monkeypatch.setenv("OKS_PROFILE", "default")
    stale = build_signed_requests_token("AK", "SK", "eu-west-2")
    save_sigv4_token(stale)

    with patch("oks_cli.cluster.build_signed_requests_token", wraps=build_signed_requests_token) as build:
        result = run_token()
    build.assert_called_once()

    token = result["status"]["token"]
    assert token.startswith("oks-sigv4-v2.")
    amz_date = datetime.strptime(decode_signed_requests_token(token)["AmzDate"], '%Y%m%dT%H%M%SZ')
    assert result["status"]["expirationTimestamp"] == (amz_date + timedelta(minutes=14)).strftime('%Y-%m-%dT%H:%M:%SZ')

    with open(get_sigv4_token_file()) as file:
        assert file.read() == stale


# Test API requests: an ak/sk profile sends a SigV4 token, never the raw ak/sk
@patch("oks_cli.utils.requests.request")
def test_api_request_uses_sigv4_for_aksk(mock_request, add_default_profile):
    mock_request.side_effect = clusters_responses()

    result = CliRunner().invoke(cli, CLUSTER_LIST)
    assert result.exit_code == 0, result.output

    headers = mock_request.call_args.kwargs["headers"]
    assert headers["Authorization"].startswith("Bearer oks-sigv4-v2.")
    assert "AccessKey" not in headers
    assert "SecretKey" not in headers


# Test API requests: an expired or foreign cached token is not used
@pytest.mark.parametrize("access_key, amz_date", [
    ("AK", "20200101T000000Z"),
    ("OTHER", datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')),
])
@patch("oks_cli.utils.requests.request")
def test_api_request_ignores_invalid_cached_token(mock_request, add_default_profile, monkeypatch, access_key, amz_date):
    monkeypatch.setenv("OKS_PROFILE", "default")
    stale = encode_signed_requests_token("oks-sigv4-v2.", {
        "AccessKey": access_key, "AmzDate": amz_date, "Region": "eu-west-2", "Signature": "ab",
    })
    save_sigv4_token(stale)
    authorizations = record_authorizations(mock_request, clusters_responses())

    result = CliRunner().invoke(cli, CLUSTER_LIST)
    assert result.exit_code == 0, result.output

    assert f"Bearer {stale}" not in authorizations
    token = authorizations[0][len("Bearer "):]
    assert decode_signed_requests_token(token)["AccessKey"] == "AK"
    with open(get_sigv4_token_file()) as file:
        assert file.read() == token


# Test API requests: the token is cached only after the API accepted it
@patch("oks_cli.utils.requests.request")
def test_api_request_caches_accepted_token(mock_request, add_default_profile):
    authorizations = record_authorizations(mock_request, clusters_responses() + clusters_responses())

    for _ in range(2):
        result = CliRunner().invoke(cli, CLUSTER_LIST)
        assert result.exit_code == 0, result.output

    assert len(authorizations) == 4
    assert authorizations[0].startswith("Bearer oks-sigv4-v2.")
    assert len(set(authorizations)) == 1

    os.environ["OKS_PROFILE"] = "default"
    assert oct(os.stat(get_sigv4_token_file()).st_mode & 0o777) == "0o600"


# Test API requests: a rejected cached token is dropped and the request retried once with a fresh one
@patch("oks_cli.utils.requests.request")
def test_api_request_retries_rejected_cached_token(mock_request, add_default_profile, monkeypatch):
    monkeypatch.setenv("OKS_PROFILE", "default")
    cached = build_signed_requests_token("AK", "SK", "eu-west-2")
    save_sigv4_token(cached)
    fresh = encode_signed_requests_token("oks-sigv4-v2.", {
        "AccessKey": "AK", "AmzDate": datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
        "Region": "eu-west-2", "Signature": "cd",
    })
    authorizations = record_authorizations(mock_request, [rejected_response()] + clusters_responses())

    with patch("oks_cli.utils.build_signed_requests_token", return_value=fresh):
        result = CliRunner().invoke(cli, CLUSTER_LIST)
    assert result.exit_code == 0, result.output

    assert authorizations == [f"Bearer {cached}", f"Bearer {fresh}", f"Bearer {fresh}"]
    with open(get_sigv4_token_file()) as file:
        assert file.read() == fresh


# Test API requests: a rejected fresh token is not cached and not retried
@patch("oks_cli.utils.requests.request")
def test_api_request_rejected_fresh_token(mock_request, add_default_profile):
    authorizations = record_authorizations(mock_request, [rejected_response()])

    result = CliRunner().invoke(cli, CLUSTER_LIST)
    assert result.exit_code != 0
    assert len(authorizations) == 1

    os.environ["OKS_PROFILE"] = "default"
    assert not os.path.exists(get_sigv4_token_file())
