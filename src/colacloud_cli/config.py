"""Configuration management for COLA Cloud CLI."""

import json
import os
from pathlib import Path
from typing import Optional

# Default configuration directory and file
CONFIG_DIR = Path.home() / ".colacloud"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Environment variable for API key
API_KEY_ENV_VAR = "COLACLOUD_API_KEY"

# API base URL
DEFAULT_API_BASE_URL = "https://app.colacloud.us/api/v1"


class Config:
    """Manages CLI configuration including API key storage."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize config manager.

        Args:
            config_path: Optional custom path to config file.
                        Defaults to ~/.colacloud/config.json
        """
        self.config_path = config_path or CONFIG_FILE
        self._config: dict = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from file if it exists."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._config = {}
        else:
            self._config = {}

    def _save(self) -> None:
        """Save configuration to file."""
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w") as f:
            json.dump(self._config, f, indent=2)

        # Set restrictive permissions on config file (contains API key)
        os.chmod(self.config_path, 0o600)

    def get_api_key(self) -> Optional[str]:
        """Get API key from environment variable or config file.

        Environment variable takes precedence over config file.

        Returns:
            API key string or None if not configured.
        """
        # Check environment variable first
        env_key = os.environ.get(API_KEY_ENV_VAR)
        if env_key:
            return env_key

        # Fall back to config file
        return self._config.get("api_key")

    def set_api_key(self, api_key: str) -> None:
        """Save API key to config file.

        Args:
            api_key: The API key to save.
        """
        self._config["api_key"] = api_key
        self._save()

    def get_api_base_url(self) -> str:
        """Get API base URL from config or use default.

        Returns:
            API base URL string.
        """
        return self._config.get("api_base_url", DEFAULT_API_BASE_URL)

    def set_api_base_url(self, url: str) -> None:
        """Save API base URL to config file.

        Args:
            url: The API base URL to save.
        """
        self._config["api_base_url"] = url
        self._save()

    def clear(self) -> None:
        """Clear all configuration."""
        self._config = {}
        if self.config_path.exists():
            self.config_path.unlink()

    def to_dict(self) -> dict:
        """Return configuration as dictionary (with masked API key).

        Returns:
            Configuration dictionary with sensitive values masked.
        """
        result = dict(self._config)
        if "api_key" in result:
            key = result["api_key"]
            if len(key) > 8:
                result["api_key"] = key[:4] + "*" * (len(key) - 8) + key[-4:]
            else:
                result["api_key"] = "*" * len(key)

        # Add source information
        if os.environ.get(API_KEY_ENV_VAR):
            result["api_key_source"] = "environment variable"
        elif self._config.get("api_key"):
            result["api_key_source"] = "config file"
        else:
            result["api_key_source"] = "not configured"

        result["config_file"] = str(self.config_path)
        return result


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance.

    Returns:
        Config instance.
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
