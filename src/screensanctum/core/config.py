"""Configuration management for ScreenSanctum."""

import json
from pathlib import Path
from typing import Dict, Any
import platformdirs


def get_app_dirs() -> Dict[str, Path]:
    """Get application directories for config and data storage.

    Returns:
        Dict containing 'config_dir' and 'data_dir' Path objects.
    """
    config_dir = Path(platformdirs.user_config_dir("ScreenSanctum"))
    data_dir = Path(platformdirs.user_data_dir("ScreenSanctum"))

    # Ensure directories exist
    config_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    return {
        "config_dir": config_dir,
        "data_dir": data_dir,
    }


def get_config_path() -> Path:
    """Get the path to the configuration file.

    Returns:
        Path to config.json
    """
    dirs = get_app_dirs()
    return dirs["config_dir"] / "config.json"


def load_config() -> Dict[str, Any]:
    """Load configuration from config file.

    Returns:
        Dictionary containing configuration settings.
        Returns default config if file doesn't exist.
    """
    config_path = get_config_path()

    if not config_path.exists():
        # Return default configuration
        return {
            "app_version": "0.1.0",
            "detection": {
                "enabled": True,
                "auto_detect_on_load": True,
            },
            "redaction": {
                "color": "#000000",
                "opacity": 1.0,
            },
            "ui": {
                "theme": "system",
                "show_sidebar": True,
            },
        }

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading config: {e}")
        return {}


def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to config file.

    Args:
        config: Dictionary containing configuration settings.

    Returns:
        True if successful, False otherwise.
    """
    config_path = get_config_path()

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except (IOError, TypeError) as e:
        print(f"Error saving config: {e}")
        return False
