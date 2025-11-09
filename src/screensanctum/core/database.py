"""Thread-safe SQLite configuration database for ScreenSanctum.

This module provides a thread-safe configuration storage system using SQLite
to prevent race conditions that occur when multiple components (API, GUI, CLI,
Workers) access config.json simultaneously.
"""

import sqlite3
import json
import threading
import os
from dataclasses import asdict
from pathlib import Path
from typing import List
import platformdirs

# Import all config dataclasses
from screensanctum.core.config import (
    AppConfig,
    RedactionTemplate,
    TemplateDetectors,
    TemplateStyle,
    TemplateIgnore,
    TemplateExport,
    CustomRule,
)
from screensanctum.core.redaction import RedactionStyle

# Define database path using platformdirs
_config_dir = Path(platformdirs.user_config_dir("ScreenSanctum"))
_config_dir.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = _config_dir / "config.sqlite"

# Thread lock for all database operations
db_lock = threading.Lock()


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

    # Deserialize custom rules
    custom_rules = []
    custom_rules_data = data.get("custom_rules", [])
    for rule_data in custom_rules_data:
        if isinstance(rule_data, dict):
            custom_rules.append(CustomRule(**rule_data))

    return RedactionTemplate(
        id=data.get("id", "tpl_custom"),
        name=data.get("name", "Custom Template"),
        version=data.get("version", 1),
        detectors=detectors,
        ignore=ignore,
        style=style,
        export=export,
        ocr_conf=data.get("ocr_conf", 60),
        url_flag_query_params=data.get("url_flag_query_params", True),
        custom_rules=custom_rules
    )


def init_db() -> None:
    """Initialize the configuration database.

    Creates the config table if it doesn't exist. If the database is empty,
    attempts to migrate data from legacy config.json file. If migration fails
    or no legacy file exists, creates a default config. This is safe to call
    multiple times.
    """
    # 1. Define paths
    config_dir = platformdirs.user_config_dir("ScreenSanctum", ensure_exists=True)
    db_path = os.path.join(config_dir, "config.sqlite")
    legacy_json_path = os.path.join(config_dir, "config.json")

    with db_lock:
        db = sqlite3.connect(db_path)
        db.execute("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, config_json TEXT)")

        # 2. Check if DB is empty
        cursor = db.execute("SELECT config_json FROM config WHERE id = 1")
        existing_config = cursor.fetchone()

        if existing_config is None:
            # DB is new. Check for a legacy JSON file to migrate.
            if os.path.exists(legacy_json_path):
                try:
                    with open(legacy_json_path, 'r') as f:
                        legacy_json_data = f.read()
                    # We just insert the raw JSON data.
                    # Deserialization and validation happens in load_config()
                    db.execute("INSERT INTO config (id, config_json) VALUES (1, ?)", (legacy_json_data,))
                    db.commit()
                    # Delete the old file *after* successful migration
                    os.remove(legacy_json_path)
                except Exception as e:
                    # If migration fails, create a default config
                    default_config = AppConfig()
                    default_config.templates = _create_default_templates()
                    default_config.active_template_id = "tpl_01_default"
                    default_config_dict = _serialize_config(default_config)
                    default_config_json = json.dumps(default_config_dict)
                    db.execute("INSERT INTO config (id, config_json) VALUES (1, ?)", (default_config_json,))
                    db.commit()
            else:
                # No legacy file, create a new default config
                default_config = AppConfig()
                default_config.templates = _create_default_templates()
                default_config.active_template_id = "tpl_01_default"
                default_config_dict = _serialize_config(default_config)
                default_config_json = json.dumps(default_config_dict)
                db.execute("INSERT INTO config (id, config_json) VALUES (1, ?)", (default_config_json,))
                db.commit()

        db.close()


def load_config() -> AppConfig:
    """Load configuration from SQLite database.

    This function is thread-safe and will block if another thread is
    accessing the database.

    Returns:
        AppConfig object with current settings.
        Returns default config if database is empty or corrupted.
    """
    # Ensure database is initialized
    init_db()

    with db_lock:
        try:
            conn = sqlite3.connect(str(DATABASE_PATH))
            cursor = conn.cursor()

            # Load config from database
            cursor.execute("SELECT config_json FROM config WHERE id = 1")
            row = cursor.fetchone()
            conn.close()

            if not row:
                # Return default config if not found
                config = AppConfig()
                config.templates = _create_default_templates()
                config.active_template_id = "tpl_01_default"
                return config

            # Deserialize JSON
            config_json = row[0]
            data = json.loads(config_json)

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

        except (json.JSONDecodeError, sqlite3.Error, KeyError, TypeError) as e:
            print(f"Error loading config from database: {e}")
            # Return default config on error
            config = AppConfig()
            config.templates = _create_default_templates()
            config.active_template_id = "tpl_01_default"
            return config


def save_config(config: AppConfig) -> bool:
    """Save configuration to SQLite database.

    This function is thread-safe and will block if another thread is
    accessing the database.

    Args:
        config: AppConfig object containing settings to save.

    Returns:
        True if successful, False otherwise.
    """
    # Ensure database is initialized
    init_db()

    with db_lock:
        try:
            # Serialize config to JSON
            config_dict = _serialize_config(config)
            config_json = json.dumps(config_dict, indent=2)

            # Update database
            conn = sqlite3.connect(str(DATABASE_PATH))
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE config SET config_json = ? WHERE id = 1",
                (config_json,)
            )

            conn.commit()
            conn.close()

            return True

        except (sqlite3.Error, TypeError, json.JSONEncodeError) as e:
            print(f"Error saving config to database: {e}")
            return False


def _serialize_config(config: AppConfig) -> dict:
    """Serialize AppConfig to a dictionary for JSON storage.

    Args:
        config: AppConfig object to serialize.

    Returns:
        Dictionary representation of the config.
    """
    from dataclasses import asdict

    # Convert dataclass to dict
    config_dict = asdict(config)

    # Convert RedactionStyle enums to strings for JSON serialization
    for template in config_dict.get("templates", []):
        if "style" in template and "default" in template["style"]:
            style_value = template["style"]["default"]
            if hasattr(style_value, "name"):
                template["style"]["default"] = style_value.name

    return config_dict
