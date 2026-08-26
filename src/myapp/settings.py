import json
from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QSizePolicy,
    QSpinBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette

DEFAULT_SETTINGS: dict[str, dict[str, Any]] = {
    "JobVault Libre Extension": {
        "jobvault_app_port": 8765,
    },
}


def load_settings(path: Path) -> dict[str, dict[str, Any]]:
    """
    Load all settings from a JSON configuration file.

    If the file does not exist, or contains invalid JSON, return the
    default settings.

    Missing sections/settings are filled from DEFAULT_SETTINGS so that
    newly introduced settings are available to older configuration files.
    """
    settings: dict[str, dict[str, Any]] = {}

    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as file:
                loaded = json.load(file)

            if isinstance(loaded, dict):
                settings = loaded
        except (OSError, json.JSONDecodeError):
            pass

    # Add missing defaults without removing user-defined settings.
    for section, defaults in DEFAULT_SETTINGS.items():
        if not isinstance(settings.get(section), dict):
            settings[section] = {}

        for key, default_value in defaults.items():
            settings[section].setdefault(key, default_value)

    return settings


def save_settings(path: Path, settings: dict[str, dict[str, Any]]) -> None:
    """
    Save all settings as human-readable JSON.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            settings,
            file,
            indent=4,
            ensure_ascii=False,
            )
        file.write("\n")


class SettingsPage(QWidget):
    """
    Application settings page.

    Settings are stored in the user's profile config.json file and are
    intentionally kept human-readable so users can edit the file manually.
    """

    def __init__(
        self,
        config_path: Path,
        parent: QWidget | None = None,
        ) -> None:
        super().__init__(parent)

        self.config_path = config_path
        self.settings = load_settings(self.config_path)

        self._build_ui()
        self._apply_stylesheet()
        self._load_settings_into_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # ── Page title ──────────────────────────────────────────────────────
        title = QLabel("Settings")
        title.setObjectName("settingsTitle")

        main_layout.addWidget(title)

        # ── JobVault Libre Extension section ─────────────────────────────────
        section = QFrame()
        section.setObjectName("settingsSection")
        section.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum,
            )

        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(16, 14, 16, 16)
        section_layout.setSpacing(14)

        section_title = QLabel("JobVault Libre Extension")
        section_title.setObjectName("settingsSectionTitle")

        section_layout.addWidget(section_title)

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        port_label = QLabel("JobVault app port")
        port_label.setObjectName("settingsLabel")
        port_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
            )

        self.port_spinbox = QSpinBox()
        self.port_spinbox.setObjectName("settingsSpinBox")
        self.port_spinbox.setRange(1, 65535)
        self.port_spinbox.setSingleStep(1)
        self.port_spinbox.setToolTip(
            "TCP port used by the JobVault Libre browser extension."
            )

        form.addWidget(port_label, 0, 0)
        form.addWidget(self.port_spinbox, 0, 1)

        # Keep the form from stretching the setting itself unnecessarily.
        form.setColumnStretch(0, 0)
        form.setColumnStretch(1, 1)

        section_layout.addLayout(form)

        main_layout.addWidget(section)

        # ── Action buttons ──────────────────────────────────────────────────
        actions = QHBoxLayout()
        actions.addStretch()

        self.reset_button = QPushButton("Reset to defaults")
        self.reset_button.setObjectName("cancelBtn")
        self.reset_button.setCursor(
            Qt.CursorShape.PointingHandCursor
            )
        self.reset_button.setFixedHeight(36)
        self.reset_button.clicked.connect(self._reset_to_defaults)

        self.apply_button = QPushButton("Apply")
        self.apply_button.setObjectName("saveBtn")
        self.apply_button.setCursor(
            Qt.CursorShape.PointingHandCursor
            )
        self.apply_button.setFixedHeight(36)
        self.apply_button.clicked.connect(self._apply_settings)

        actions.addWidget(self.reset_button)
        actions.addSpacing(8)
        actions.addWidget(self.apply_button)

        main_layout.addLayout(actions)
        main_layout.addStretch(1)

    def _load_settings_into_ui(self) -> None:
        """Populate the widgets from the currently loaded settings."""
        extension_settings = self.settings["JobVault Libre Extension"]

        port = extension_settings.get(
            "jobvault_app_port",
            DEFAULT_SETTINGS["JobVault Libre Extension"]["jobvault_app_port"],
            )

        try:
            port = int(port)
        except (TypeError, ValueError):
            port = DEFAULT_SETTINGS[
                "JobVault Libre Extension"
                ]["jobvault_app_port"]

        if not 1 <= port <= 65535:
            port = DEFAULT_SETTINGS[
                "JobVault Libre Extension"
                ]["jobvault_app_port"]

        self.port_spinbox.setValue(port)

    def _apply_settings(self) -> None:
        """Save the values currently shown in the settings UI."""
        self.settings["JobVault Libre Extension"][
            "jobvault_app_port"
            ] = self.port_spinbox.value()

        try:
            save_settings(self.config_path, self.settings)
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Unable to save settings",
                f"Could not save the settings file:\n{exc}",
            )
            return

        QMessageBox.information(
            self,
            "Settings applied",
            "The settings have been saved.\n\n"
            "A restart of JobVault Libre is required for the changes to take effect.",
        )

    def _reset_to_defaults(self) -> None:
        """
        Reset the UI to the default values.

        The reset is not written to disk until Apply is pressed.
        """
        defaults = DEFAULT_SETTINGS["JobVault Libre Extension"]

        self.port_spinbox.setValue(
            defaults["jobvault_app_port"]
            )

    def _apply_stylesheet(self) -> None:
        """Apply the settings page stylesheet."""
        window_bg = self.palette().color(
            QPalette.ColorRole.Window
            )

        border_color = window_bg.lighter(200)
        hover_bg = "rgba(128, 128, 128, 30)"
        dialog_bg = window_bg.lighter(110)
        highlight = self.palette().color(
            QPalette.ColorRole.Highlight
            )
        hover_highlight = highlight.darker(90).name()

        stylesheet = f"""
            /* ==================== PAGE TITLE ==================== */

            QLabel#settingsTitle {{
                font-weight: 600;
                font-size: 20px;
                color: palette(window-text);
            }}

            /* ==================== SETTINGS SECTION ==================== */

            QFrame#settingsSection {{
                background-color: {dialog_bg.name()};
                border: 1px solid {border_color.name()};
                border-radius: 8px;
            }}

            QLabel#settingsSectionTitle {{
                font-weight: 600;
                font-size: 16px;
                color: palette(window-text);
            }}

            QLabel#settingsLabel {{
                font-size: 14px;
                color: palette(window-text);
            }}

            QSpinBox#settingsSpinBox {{
                border: 1px solid {border_color.name()};
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
            }}

            QSpinBox#settingsSpinBox:hover {{
                background-color: {hover_bg};
            }}

            QSpinBox#settingsSpinBox:focus {{
                border: 1px solid palette(highlight);
            }}

            /* ==================== BUTTONS ==================== */

            QPushButton#cancelBtn {{
                border: none;
                font-size: 14px;
                padding: 8px 18px;
                border-radius: 6px;
            }}

            QPushButton#cancelBtn:hover {{
                background-color: {hover_bg};
            }}

            QPushButton#saveBtn {{
                background-color: palette(highlight);
                border: none;
                color: palette(highlighted-text);
                font-size: 14px;
                padding: 8px 18px;
                border-radius: 6px;
            }}

            QPushButton#saveBtn:hover {{
                background-color: {hover_highlight};
            }}
        """

        self.setStyleSheet(stylesheet)