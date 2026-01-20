"""Tests for configuration management."""

import json
import os
from pathlib import Path

import pytest

from colacloud_cli.config import Config, API_KEY_ENV_VAR


@pytest.fixture
def temp_config(tmp_path):
    """Create a temporary config file."""
    config_file = tmp_path / "config.json"
    return Config(config_path=config_file)


@pytest.fixture
def clean_env():
    """Ensure API key env var is not set during tests."""
    old_value = os.environ.pop(API_KEY_ENV_VAR, None)
    yield
    if old_value is not None:
        os.environ[API_KEY_ENV_VAR] = old_value


class TestConfig:
    def test_init_creates_empty_config(self, temp_config):
        """Config initializes with empty dict when no file exists."""
        assert temp_config._config == {}

    def test_set_and_get_api_key(self, temp_config, clean_env):
        """API key can be saved and retrieved."""
        temp_config.set_api_key("test_key_12345")
        assert temp_config.get_api_key() == "test_key_12345"

    def test_api_key_persists(self, tmp_path, clean_env):
        """API key persists across config instances."""
        config_file = tmp_path / "config.json"

        config1 = Config(config_path=config_file)
        config1.set_api_key("persistent_key")

        config2 = Config(config_path=config_file)
        assert config2.get_api_key() == "persistent_key"

    def test_env_var_takes_precedence(self, temp_config):
        """Environment variable takes precedence over config file."""
        temp_config.set_api_key("file_key")
        os.environ[API_KEY_ENV_VAR] = "env_key"

        try:
            assert temp_config.get_api_key() == "env_key"
        finally:
            del os.environ[API_KEY_ENV_VAR]

    def test_get_api_key_returns_none_when_not_set(self, temp_config, clean_env):
        """get_api_key returns None when no key is configured."""
        assert temp_config.get_api_key() is None

    def test_config_file_permissions(self, temp_config, clean_env):
        """Config file has restrictive permissions after save."""
        temp_config.set_api_key("secret_key")
        mode = temp_config.config_path.stat().st_mode & 0o777
        assert mode == 0o600

    def test_clear_removes_config(self, temp_config, clean_env):
        """clear() removes all configuration."""
        temp_config.set_api_key("test_key")
        temp_config.clear()

        assert temp_config.get_api_key() is None
        assert not temp_config.config_path.exists()

    def test_to_dict_masks_api_key(self, temp_config, clean_env):
        """to_dict() masks the API key."""
        temp_config.set_api_key("sk_live_1234567890abcdef")
        result = temp_config.to_dict()

        # Key is masked: first 4 chars + asterisks + last 4 chars
        assert result["api_key"].startswith("sk_l")
        assert result["api_key"].endswith("cdef")
        assert "*" in result["api_key"]
        assert result["api_key_source"] == "config file"

    def test_to_dict_short_key_fully_masked(self, temp_config, clean_env):
        """Short API keys are fully masked."""
        temp_config.set_api_key("short")
        result = temp_config.to_dict()

        assert result["api_key"] == "*****"

    def test_get_api_base_url_default(self, temp_config):
        """Default API base URL is returned."""
        assert temp_config.get_api_base_url() == "https://app.colacloud.us/api/v1"

    def test_set_api_base_url(self, temp_config):
        """Custom API base URL can be set."""
        temp_config.set_api_base_url("https://custom.example.com/api")
        assert temp_config.get_api_base_url() == "https://custom.example.com/api"

    def test_handles_corrupted_config_file(self, tmp_path, clean_env):
        """Config handles corrupted JSON gracefully."""
        config_file = tmp_path / "config.json"
        config_file.write_text("not valid json {{{")

        config = Config(config_path=config_file)
        assert config._config == {}
        assert config.get_api_key() is None
