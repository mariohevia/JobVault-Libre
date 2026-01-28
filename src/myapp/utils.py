import os
import sys
import re
from pathlib import Path

from PyQt6.QtWidgets import (
    QDateEdit,
    QComboBox,
    QAbstractSpinBox,
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QDate

class NoScrollDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set default configuration
        self.setDisplayFormat("dd/MM/yyyy")
        self.setCalendarPopup(True)
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

def get_app_paths_for_user(app_name: str, user_id: str) -> dict[str, Path]:
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