"""Tests for pgdrift.config module."""

from pathlib import Path

import pytest
import yaml

from pgdrift.config import Config, DatabaseProfile


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    data = {
        "profiles": {
            "production": {
                "host": "prod.db.example.com",
                "port": 5432,
                "dbname": "myapp",
                "user": "readonly",
                "password": "s3cr3t",
            },
            "staging": {
                "host": "staging.db.example.com",
                "dbname": "myapp_staging",
                "user": "readonly",
            },
        }
    }
    cfg_path = tmp_path / "pgdrift.yml"
    cfg_path.write_text(yaml.dump(data))
    return cfg_path


def test_load_returns_config(config_file: Path) -> None:
    config = Config.load(config_file)
    assert isinstance(config, Config)
    assert "production" in config.profiles
    assert "staging" in config.profiles


def test_profile_fields(config_file: Path) -> None:
    config = Config.load(config_file)
    prod = config.get_profile("production")
    assert isinstance(prod, DatabaseProfile)
    assert prod.host == "prod.db.example.com"
    assert prod.port == 5432
    assert prod.dbname == "myapp"
    assert prod.password == "s3cr3t"


def test_dsn_format(config_file: Path) -> None:
    config = Config.load(config_file)
    prod = config.get_profile("production")
    dsn = prod.dsn()
    assert "host=prod.db.example.com" in dsn
    assert "dbname=myapp" in dsn
    assert "password=s3cr3t" in dsn


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        Config.load(tmp_path / "nonexistent.yml")


def test_empty_profiles_raises(tmp_path: Path) -> None:
    cfg_path = tmp_path / "pgdrift.yml"
    cfg_path.write_text(yaml.dump({"profiles": {}}))
    with pytest.raises(ValueError, match="at least one profile"):
        Config.load(cfg_path)


def test_get_profile_missing_raises(config_file: Path) -> None:
    config = Config.load(config_file)
    with pytest.raises(KeyError, match="development"):
        config.get_profile("development")
