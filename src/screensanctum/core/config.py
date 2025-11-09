"""Configuration management for ScreenSanctum."""

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List
import platformdirs
from screensanctum.core.redaction import RedactionStyle


@dataclass
class CustomRule:
    """A custom regex pattern for PII detection."""

    name: str = "New Rule"
    regex: str = "PATTERN_HERE"


@dataclass
class TemplateDetectors:
    """Configures which detectors are enabled for a template."""

    email: bool = True
    phone: bool = True
    ipv4: bool = True
    hostname: bool = True
    url: bool = True
    face: bool = False  # Stub for later


@dataclass
class TemplateStyle:
    """Configures redaction styles for a template."""

    default: RedactionStyle = RedactionStyle.SOLID


@dataclass
class TemplateIgnore:
    """Configures ignore lists for a template."""

    emails: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)


@dataclass
class TemplateExport:
    """Configures export settings for a template."""

    format: str = "png"
    flatten: bool = True
    strip_metadata: bool = True
    filename_pattern: str = "{name}_redacted.png"


@dataclass
class RedactionTemplate:
    """A complete redaction policy template."""

    id: str
    name: str
    version: int = 1
    detectors: TemplateDetectors = field(default_factory=TemplateDetectors)
    ignore: TemplateIgnore = field(default_factory=TemplateIgnore)
    style: TemplateStyle = field(default_factory=TemplateStyle)
    export: TemplateExport = field(default_factory=TemplateExport)
    ocr_conf: int = 60
    url_flag_query_params: bool = True
    custom_rules: List[CustomRule] = field(default_factory=list)


@dataclass
class AppConfig:
    """Application configuration settings."""

    templates: List[RedactionTemplate] = field(default_factory=list)
    active_template_id: str = "tpl_01_default"
    ocr_confidence_threshold: int = 60
    show_sidebar: bool = True
    theme: str = "system"  # "system", "light", or "dark"
    last_save_directory: str = ""
    enable_audit_logs: bool = True
    api_keys: List[str] = field(default_factory=list)


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



# Import thread-safe database functions
# These replace the old JSON-based load_config and save_config functions
# to fix the critical config race condition bug
from screensanctum.core.database import load_config, save_config  # noqa: E402
