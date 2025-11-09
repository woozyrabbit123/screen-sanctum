"""Configuration management for ScreenSanctum."""

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List
import platformdirs
from screensanctum.core.redaction import RedactionStyle


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


def get_config_path() -> Path:
    """Get the path to the configuration file.

    Returns:
        Path to config.json
    """
    dirs = get_app_dirs()
    return dirs["config_dir"] / "config.json"


def _create_default_templates() -> List[RedactionTemplate]:
    """Create the built-in default templates.

    Returns:
        List of default RedactionTemplate objects.
    """
    return [
        RedactionTemplate(
            id="tpl_01_default",
            name="Default (Solid)",
            detectors=TemplateDetectors(),
            style=TemplateStyle(default=RedactionStyle.SOLID),
            ignore=TemplateIgnore(),
            ocr_conf=60,
            url_flag_query_params=True
        ),
        RedactionTemplate(
            id="tpl_02_social_share",
            name="Social Share Safe",
            detectors=TemplateDetectors(),
            style=TemplateStyle(default=RedactionStyle.SOLID),
            ignore=TemplateIgnore(),
            ocr_conf=70,  # Higher confidence for social sharing
            url_flag_query_params=True
        ),
        RedactionTemplate(
            id="tpl_03_bug_report",
            name="Bug Report Safe",
            detectors=TemplateDetectors(),
            style=TemplateStyle(default=RedactionStyle.BLUR),
            ignore=TemplateIgnore(),
            ocr_conf=60,
            url_flag_query_params=False  # Allow URLs in bug reports
        ),
    ]


def _deserialize_template(data: dict) -> RedactionTemplate:
    """Deserialize a template from JSON data.

    Args:
        data: Dictionary containing template data.

    Returns:
        RedactionTemplate object.
    """
    # Deserialize nested objects
    detectors = TemplateDetectors(**data.get("detectors", {}))
    ignore = TemplateIgnore(**data.get("ignore", {}))

    # Handle RedactionStyle enum
    style_data = data.get("style", {})
    default_style = style_data.get("default", "SOLID")
    if isinstance(default_style, str):
        # Convert string to enum
        default_style = RedactionStyle[default_style]
    style = TemplateStyle(default=default_style)

    export_data = data.get("export", {})
    export = TemplateExport(**export_data)

    return RedactionTemplate(
        id=data.get("id", "tpl_custom"),
        name=data.get("name", "Custom Template"),
        version=data.get("version", 1),
        detectors=detectors,
        ignore=ignore,
        style=style,
        export=export,
        ocr_conf=data.get("ocr_conf", 60),
        url_flag_query_params=data.get("url_flag_query_params", True)
    )


def load_config() -> AppConfig:
    """Load configuration from config file.

    Returns:
        AppConfig object with settings.
        Returns default config with built-in templates if file doesn't exist.
    """
    config_path = get_config_path()

    if not config_path.exists():
        # Return default configuration with built-in templates
        config = AppConfig()
        config.templates = _create_default_templates()
        config.active_template_id = "tpl_01_default"
        return config

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Deserialize templates
        templates = []
        templates_data = data.get("templates", [])
        for tpl_data in templates_data:
            try:
                templates.append(_deserialize_template(tpl_data))
            except Exception as e:
                print(f"Error deserializing template: {e}")
                continue

        # If no templates loaded, create defaults
        if not templates:
            templates = _create_default_templates()

        # Create AppConfig from loaded data
        config = AppConfig(
            templates=templates,
            active_template_id=data.get("active_template_id", "tpl_01_default"),
            ocr_confidence_threshold=data.get("ocr_confidence_threshold", 60),
            show_sidebar=data.get("show_sidebar", True),
            theme=data.get("theme", "system"),
            last_save_directory=data.get("last_save_directory", ""),
            enable_audit_logs=data.get("enable_audit_logs", True),
            api_keys=data.get("api_keys", []),
        )

        # Ensure active_template_id is valid
        template_ids = [t.id for t in config.templates]
        if config.active_template_id not in template_ids:
            config.active_template_id = template_ids[0] if template_ids else "tpl_01_default"

        return config

    except (json.JSONDecodeError, IOError, KeyError, TypeError) as e:
        print(f"Error loading config: {e}")
        # Return default config with built-in templates on error
        config = AppConfig()
        config.templates = _create_default_templates()
        config.active_template_id = "tpl_01_default"
        return config


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

        # Convert RedactionStyle enums to strings for JSON serialization
        for template in config_dict.get("templates", []):
            if "style" in template and "default" in template["style"]:
                style_value = template["style"]["default"]
                if hasattr(style_value, "name"):
                    template["style"]["default"] = style_value.name

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2)
        return True
    except (IOError, TypeError) as e:
        print(f"Error saving config: {e}")
        return False
