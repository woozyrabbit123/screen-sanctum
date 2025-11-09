"""Configuration management for ScreenSanctum."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict
import platformdirs


@dataclass
class AppConfig:
    """Application configuration settings."""

    redaction_style: str = "blur"  # "blur", "solid", or "pixelate"
    auto_detect_on_open: bool = True
    ocr_confidence_threshold: int = 60
    show_sidebar: bool = True
    theme: str = "system"  # "system", "light", or "dark"
    last_save_directory: str = ""


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


def load_config() -> AppConfig:
    """Load configuration from config file.

    Returns:
        AppConfig object with settings.
        Returns default config if file doesn't exist or is invalid.
    """
    config_path = get_config_path()

    if not config_path.exists():
        # Return default configuration
        return AppConfig()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Create AppConfig from loaded data, using defaults for missing fields
        return AppConfig(
            redaction_style=data.get("redaction_style", "blur"),
            auto_detect_on_open=data.get("auto_detect_on_open", True),
            ocr_confidence_threshold=data.get("ocr_confidence_threshold", 60),
            show_sidebar=data.get("show_sidebar", True),
            theme=data.get("theme", "system"),
            last_save_directory=data.get("last_save_directory", ""),
        )
    except (json.JSONDecodeError, IOError, KeyError, TypeError) as e:
        print(f"Error loading config: {e}")
        # Return default config on error
        return AppConfig()


def save_config(config: AppConfig) -> bool:
    """Save configuration to config file.

    Args:
        config: AppConfig object containing settings.

    Returns:
        True if successful, False otherwise.
    """
    config_path = get_config_path()

    try:
        # Convert dataclass to dict
        config_dict = asdict(config)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2)
        return True
    except (IOError, TypeError) as e:
        print(f"Error saving config: {e}")
        return False
