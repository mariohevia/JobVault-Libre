import os
import sys
import re
import json
from pathlib import Path
from datetime import date
from typing import Any, Dict, Tuple

from PyQt6.QtWidgets import (
    QDateEdit,
    QComboBox,
    QAbstractSpinBox,
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QDate

from myapp.exceptions import ConfigurationFormatError

class NoScrollDateEdit(QDateEdit):
    def __init__(self, parent=None, date=None):
        super().__init__(parent)
        # Set default configuration
        self.setDisplayFormat("dd/MM/yyyy")
        self.setCalendarPopup(True)
        if date is QDate:
            self.setDate(date)
        else:
            self.setDate(QDate.currentDate())
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

    def wheelEvent(self, event):
        # Ignore wheel events
        event.ignore()

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        # Ignore wheel events
        event.ignore()

# TODO: Remove resource_path, first ensure it won't be needed anymore
def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return str(Path(sys._MEIPASS) / relative_path)
    return str(Path(relative_path).resolve())

def today_year_month() -> Tuple[int, int]:
    d = date.today()
    return d.year, d.month

def _safe_slug(value: str) -> str:
    # filesystem-safe: letters/numbers/_/-
    value = value.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9_-]", "", value)
    return value or "default"

def get_app_data_dir(app_name: str) -> Path:
    """
    Return an OS-appropriate per-user application data directory.
    The directory is created if it does not exist.
    """
    if sys.platform.startswith("win"):
        base_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support"
    else:
        # TODO: Consider separating data from cache and configurations into XDG_CONFIG_HOME and XDG_CACHE_HOME.
        base_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    app_dir = base_dir / app_name
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

def get_app_paths_for_user(app_name: str, user_id: str) -> Dict[str, Path]:
    base = get_app_data_dir(app_name) 
    profiles_dir = base / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)

    pid = _safe_slug(str(user_id))
    profile_dir = profiles_dir / pid
    profile_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "base": base,
        "users": profiles_dir,
        "user": profile_dir,
        "db": profile_dir / "database.sqlite",
        "config": profile_dir / "config.json",
        "cache": profile_dir / "cache",
    }
    paths["cache"].mkdir(parents=True, exist_ok=True)
    return paths

def save_full_config(config_path: str, full_cfg: Dict[str, Any]) -> None:
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(full_cfg, f, indent=2, ensure_ascii=False)

def load_full_config(config_path):
    if not config_path:
        raise RuntimeError("Configuration path not found")

    if not os.path.exists(config_path):
        # TODO: create an empty config with all the proper sections and default values from the YAML
        empty_config = {
            "cv_config":{"sections": {}}
            }

        save_full_config(config_path, empty_config)
        return empty_config
    
    with open(config_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)

        except json.JSONDecodeError as e:
            raise ConfigurationFormatError(
                f"Invalid JSON configuration file: {config_path}"
            ) from e

    if not isinstance(data, dict):
        raise ConfigurationFormatError("Invalid configuration file format")

    if "cv_config" not in data or not isinstance(data.get("cv_config"), dict):
        raise ConfigurationFormatError("Incorrect 'cv_config' format in configuration file")

    # TODO: Check that all sections have their configuration in a correct format
    if "sections" not in data.get("cv_config") or not isinstance(data["cv_config"].get("sections"), dict):
        raise ConfigurationFormatError("Incorrect 'sections' format in configuration file")

    return data

def load_cv_config(config_path: str) -> Dict[str, Any]:
    cv_config = load_full_config(config_path).get("cv_config")

    return cv_config

# TODO: use this to create all icons
# I can safely bundle icons from:
# Tabler Icons (MIT) https://tabler.io/icons
# Feather Icons (MIT)
# Material Symbols (Outlined)

def themed_icon_with_fallback(theme_name: str, fallback_path: str) -> QIcon:
    icon = QIcon.fromTheme(theme_name)
    if icon.isNull():
        icon = QIcon(fallback_path)
    return icon
    
def palette_color_to_rgba(c, a=100):
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {a})"