from __future__ import annotations

from pathlib import Path
import json

from importlib import resources

import yaml
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QFont
from PyQt6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
)


class SectionCard(QWidget):
    """
    Simple card showing a section defined in section_types.yml
    plus basic info from the user profile (enabled, item count).
    """

    def __init__(
        self,
        section_def: dict,
        user_section: dict | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.section_def = section_def
        self.user_section = user_section or {}

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Frame to mimic a card-like look, similar to JobApplicationCard style
        frame = QFrame(self)
        frame.setObjectName("sectionCardFrame")
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QFrame.Shadow.Raised)

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(10, 8, 10, 8)
        frame_layout.setSpacing(4)

        # --- Derive data from defs + user profile ---

        section_type = self.section_def.get("type", "")
        default_title = self.section_def.get("default_title", section_type.title())

        title_override = self.user_section.get("title_override")
        title = title_override or default_title

        # Enabled / never_use flags
        enabled_by_default = bool(self.section_def.get("enabled_by_default", True))
        enabled = self.user_section.get("enabled", enabled_by_default)
        never_use = bool(self.user_section.get("never_use", False))

        # Item count
        items = self.user_section.get("items", []) or []
        item_label_def = self.section_def.get("item_label", {}) or {}
        singular_label = item_label_def.get("singular", "Item")
        plural_label = item_label_def.get("plural", "Items")

        count = len(items)
        if count == 1:
            count_text = f"1 {singular_label}"
        else:
            count_text = f"{count} {plural_label}"

        # Status text
        if never_use:
            status_text = "Never use"
        else:
            status_text = "Enabled" if enabled else "Disabled"

        # --- Header row (title + status) ---

        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        title_label = QLabel(title, frame)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)

        header_row.addWidget(title_label, stretch=1)

        status_label = QLabel(status_text, frame)
        status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        status_label.setObjectName("sectionStatusLabel")

        header_row.addWidget(status_label, stretch=0)

        frame_layout.addLayout(header_row)

        # --- Secondary row (type + item count) ---

        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)

        type_label = QLabel(f"Type: {section_type}", frame)
        type_label.setObjectName("sectionTypeLabel")

        count_label = QLabel(count_text, frame)
        count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        count_label.setObjectName("sectionCountLabel")

        meta_row.addWidget(type_label, stretch=1)
        meta_row.addWidget(count_label, stretch=0)

        frame_layout.addLayout(meta_row)

        layout.addWidget(frame)


class ProfilePage(QWidget):
    def __init__(
        self,
        palette: QPalette,
        paths: dict[str, Path],
        parent: QWidget | None = None,
    ):
        """
        :param palette: existing app palette
        :param paths:   dict from get_app_paths_for_user (must contain "config")
        """
        super().__init__(parent)
        self.palette = palette
        self.paths = paths

        self.section_defs: list[dict] = []
        self.user_profile: dict = {}

        self._init_ui()
        self._load_data_and_build_section_list()

    def _init_ui(self) -> None:
        # Outer frame to give a card-like outline
        self.frame = QFrame(self)
        self.frame.setObjectName("cardFrame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)

        # Main layout for this widget
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.frame)

        # Layout inside the frame
        self.layout = QVBoxLayout(self.frame)
        self.layout.setContentsMargins(12, 10, 12, 10)
        self.layout.setSpacing(8)

        # --- Header ---
        header_title = QLabel("Profile Overview", self.frame)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        header_title.setFont(title_font)

        header_subtext = QLabel("Manage global CV content and defaults", self.frame)
        sub_font = QFont()
        sub_font.setPointSize(10)
        header_subtext.setFont(sub_font)
        header_subtext.setStyleSheet("color: gray;")  # tweak via QSS later if you prefer

        self.layout.addWidget(header_title)
        self.layout.addWidget(header_subtext)

        # --- Scroll area for section cards ---

        self.scroll_area = QScrollArea(self.frame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.section_list_container = QWidget(self.scroll_area)
        self.section_list_layout = QVBoxLayout(self.section_list_container)
        self.section_list_layout.setContentsMargins(0, 8, 0, 0)
        self.section_list_layout.setSpacing(8)

        self.scroll_area.setWidget(self.section_list_container)

        self.layout.addWidget(self.scroll_area)

        # Spacer at the bottom
        self.layout.addStretch(1)

    # ----------------------
    # Data loading
    # ----------------------

    def _load_data_and_build_section_list(self) -> None:
        self.section_defs = self._load_section_types_from_yaml()
        self.user_profile = self._load_user_profile_from_json(self.paths.get("config"))

        # Clear previous cards if any
        while self.section_list_layout.count():
            item = self.section_list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        # Build cards from YAML definitions
        user_sections_by_type = self._index_user_sections_by_type(self.user_profile)

        for section_def in self.section_defs:
            section_type = section_def.get("type")
            user_section = user_sections_by_type.get(section_type)

            card = SectionCard(section_def, user_section, parent=self.section_list_container)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            self.section_list_layout.addWidget(card)

        self.section_list_layout.addStretch(1)

    @staticmethod
    def _index_user_sections_by_type(user_profile: dict) -> dict[str, dict]:
        result: dict[str, dict] = {}
        sections = user_profile.get("sections", []) or []
        for sec in sections:
            sec_type = sec.get("type")
            if sec_type:
                result[sec_type] = sec
        return result

    @staticmethod
    def _load_user_profile_from_json(config_path: Path | None) -> dict:
        if not config_path:
            return {}

        if not config_path.exists():
            # If there is no user profile yet, treat as empty profile
            return {}

        try:
            with config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
        except Exception:
            # In case of parse errors, fail gracefully and show no data
            return {}

    @staticmethod
    def _load_section_types_from_yaml() -> list[dict]:
        """
        Load the static section schema from myapp/resources/section_types.yml
        Adjust "myapp.resources" if your package name differs.
        """
        try:
            with resources.files("myapp.resources").joinpath("section_types.yml").open(
                "r",
                encoding="utf-8",
            ) as f:
                data = yaml.safe_load(f) or {}
        except FileNotFoundError:
            return []
        except Exception:
            # Fail gracefully if YAML is invalid
            return []

        sections = data.get("sections", []) or []
        if not isinstance(sections, list):
            return []
        return sections
