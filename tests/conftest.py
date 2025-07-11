import pytest
import json
import os

@pytest.fixture(autouse=True)
def fake_config(monkeypatch, tmp_path):
    fake_home = tmp_path
    config_dir = fake_home / ".oks_cli"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.json"

    cache_dir = fake_home / ".oks_cli" / "cache"
    cache_dir.mkdir(parents=True)

    def fake_expanduser(path):
        if path == "~":
            return str(fake_home)
        elif path == "~/.oks_cli/config.json":
            return str(config_file)
        elif path == "~/.oks_cli":
            return str(config_dir)

    monkeypatch.setattr("os.path.expanduser", fake_expanduser)

@pytest.fixture()
def add_default_profile():
    config_path = os.path.expanduser("~/.oks_cli/config.json")

    with open(config_path, 'w') as file:
            profiles = {
                "default": {
                    "region_name": "eu-west-2",
                    "type": "ak/sk",
                    "access_key": "AK",
                    "secret_key": "SK",
                    "jwt": False
                }
            }
            profiles = json.dumps(profiles)
            file.write(profiles)