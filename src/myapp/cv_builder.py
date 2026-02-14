from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QToolButton,
    QLineEdit,
    QFrame,
    QCompleter,
    QAbstractItemView,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
    QGroupBox,
    QMessageBox,
)

from PyQt6.QtGui import QIcon, QPalette, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QStringListModel, QEvent

from myapp.database import JobDatabase
from myapp.utils import (
    load_section_names_from_yaml, 
    load_cv_config,
    NoScrollDateEdit, 
    NoScrollComboBox,
    load_full_config,
    save_full_config,
    )

from myapp.cv_config import (
    _field_default_value,
    _ItemEditor,
    SectionSettingsOverlay,
)

SEARCH_ICON = QIcon.fromTheme("edit-find")
FILTER_ICON = QIcon.fromTheme("view-filter")

STATUS_OPTIONS = [
    "Not Applied",
    "Applied",
    "Interview Scheduled",
    "Interviewed",
    "Offer",
    "Rejected",
    "Withdrawn",
    ]

JOB_TYPE_OPTIONS = [
    "Full time",
    "Part time",
    "Contract",
    ]

WORK_ARRANGEMENT_OPTIONS = [
    "On-site", 
    "Hybrid", 
    "Remote"
    ]

STATUS_COLORS = {
    "Not Applied": "#256D6D",
    "Applied": "#3B82F6",
    "Interview Scheduled": "#F59E0B",
    "Interviewed": "#8B5CF6",
    "Offer": "#2b7a2b",
    "Rejected": "#EF4444",
    "Withdrawn": "#6B7280",
    }

SectionDef = Dict[str, Any]
SectionCfg = Dict[str, Any]

class CVListPage(QWidget):

    create_cv_clicked = pyqtSignal()

    def __init__(
        self,
        db: "JobDatabase",
        palette: QPalette,
        paths: Dict[str, Path],
        parent: QWidget | None = None,
        ):
        super().__init__(parent)

        self.db = db
        self.palette = palette
        self.paths = paths

        self._build_ui()
        self._load_data()

    # ---------------- UI ---------------- #

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Top bar
        top_bar = QHBoxLayout()

        title_label = QLabel("Curriculum Vitae")
        title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        title_label.setStyleSheet("font-size: 18px; font-weight: 600;")

        add_button = QPushButton("Create CV")
        add_button.setFixedHeight(32)
        add_button.clicked.connect(self._on_create_cv)

        top_bar.addWidget(title_label)
        top_bar.addStretch()
        top_bar.addWidget(add_button)

        main_layout.addLayout(top_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Title",
            "Created",
            "Updated",
            "Newest Version ID",
            "Group ID",
            "Actions",
        ])

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)

        main_layout.addWidget(self.table)

    # ---------------- Data ---------------- #

    def _load_data(self) -> None:
        groups = self.db.get_all_cv_groups()
        self.table.setRowCount(len(groups))

        for row, (
            group_id,
            title,
            created_at,
            updated_at,
            newest_version_id,
        ) in enumerate(groups):

            self.table.setItem(row, 0, QTableWidgetItem(title))
            self.table.setItem(row, 1, QTableWidgetItem(created_at))
            self.table.setItem(row, 2, QTableWidgetItem(updated_at))
            self.table.setItem(
                row,
                3,
                QTableWidgetItem(str(newest_version_id) if newest_version_id else "")
            )
            self.table.setItem(row, 4, QTableWidgetItem(str(group_id)))

            self.table.setCellWidget(row, 5, self._create_actions_cell())

    # ---------------- Handlers ---------------- #

    def _on_create_cv(self) -> None:
        self.create_cv_clicked.emit()

    # ---------------- Helpers ---------------- #

    def _create_actions_cell(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        view_btn = QToolButton()
        view_btn.setIcon(QIcon.fromTheme("document-open"))
        view_btn.setToolTip("View CV")

        edit_btn = QToolButton()
        edit_btn.setIcon(QIcon.fromTheme("document-edit"))
        edit_btn.setToolTip("Edit CV")

        delete_btn = QToolButton()
        delete_btn.setIcon(QIcon.fromTheme("edit-delete"))
        delete_btn.setToolTip("Delete CV")

        layout.addWidget(view_btn)
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)

        return container

    def _set_column_widths(self) -> None:
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        self.table.resizeColumnsToContents()
        total_width = self.table.width()
        current_widths = [self.table.columnWidth(i) for i in range(self.table.columnCount())]
        current_total = sum(current_widths)
        extra_space = total_width - current_total

        for i in range(self.table.columnCount()):
            proportion = current_widths[i] / current_total
            self.table.setColumnWidth(i, int(current_widths[i] + proportion * extra_space))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._set_column_widths()


class CVTopNavigator(QWidget):
    """Compact top navigation bar for CV builder with tabs"""
    
    section_selected = pyqtSignal(str)  # Emits section name
    back_clicked = pyqtSignal()
    
    def __init__(
        self, 
        section_defs: list,
        parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.section_defs = section_defs
        self.current_section = None
        
        self._build_ui()
        
    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(8)
        
        # Top row: Back button and title
        top_row = QHBoxLayout()
        
        # Back button
        back_btn = QPushButton("Cancel")
        back_btn.clicked.connect(self.back_clicked.emit)
        back_btn.setFixedHeight(32)
        back_btn.setFixedWidth(80)
        
        # Title input
        title_label = QLabel("Title:")
        title_label.setStyleSheet("font-weight: 600;")
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter CV title")
        self.title_input.setFixedHeight(32)
        self.title_input.setMaximumWidth(300)
        
        top_row.addWidget(back_btn)
        top_row.addSpacing(12)
        top_row.addWidget(title_label)
        top_row.addWidget(self.title_input)
        top_row.addStretch()
        
        main_layout.addLayout(top_row)
        
        # Navigation tabs row
        nav_row = QHBoxLayout()
        nav_row.setSpacing(0)
        
        self.nav_buttons = {}
        
        # Add Target Application button
        target_btn = self._create_nav_button("target_application", "Target Application")
        nav_row.addWidget(target_btn)
        
        # Add section buttons
        for section_def in self.section_defs:
            section_name = section_def.get("name", "")
            section_label = section_def.get("default_title", section_name)
            
            btn = self._create_nav_button(section_name, section_label)
            nav_row.addWidget(btn)
        
        # Add Reorder button
        reorder_btn = self._create_nav_button("reorder_sections", "Reorder")
        nav_row.addWidget(reorder_btn)
        
        # Add Preview button
        preview_btn = self._create_nav_button("preview", "Preview")
        nav_row.addWidget(preview_btn)
        
        # nav_row.addStretch()
        
        main_layout.addLayout(nav_row)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(divider)
        
    def _create_nav_button(self, section_name: str, label: str) -> QPushButton:
        """Create a navigation button for a section"""
        btn = QPushButton(label)
        btn.setFixedHeight(28)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self._on_nav_clicked(section_name))
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 6px 12px;
                font-size: 13px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }
            QPushButton:hover {
                background-color: palette(alternate-base);
            }
            QPushButton:checked {
                background-color: palette(highlight);
                color: palette(highlighted-text);
                font-weight: 600;
            }
        """)
        
        self.nav_buttons[section_name] = btn
        return btn
    
    def _on_nav_clicked(self, section_name: str) -> None:
        """Handle navigation button click"""
        self.set_active_section(section_name)
        self.section_selected.emit(section_name)
    
    def set_active_section(self, section_name: str) -> None:
        """Set the active section in the navigation"""
        self.current_section = section_name
        
        # Update button states
        for name, btn in self.nav_buttons.items():
            btn.setChecked(name == section_name)


class SectionPlaceholderPage(QWidget):
    # TODO: Implement these pages
    """Placeholder page for each CV section"""
    
    def __init__(self, section_name: str, section_label: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.section_name = section_name
        self.section_label = section_label
        
        self._build_ui()
        
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)
        
        # Section title
        title = QLabel(self.section_label)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        
        layout.addWidget(title)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(divider)
        
        # Placeholder content
        placeholder = QLabel(f"This is a placeholder for the '{self.section_label}' section.\n\nContent will be implemented later.")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: palette(mid); font-size: 14px; padding: 40px;")
        
        layout.addWidget(placeholder, stretch=1)

def _render_value_readonly(fdef: Dict[str, Any], value: Any) -> QWidget:
    """Return a read-only QLabel (or small container) representing *value*."""
    ftype = fdef.get("type", "string")

    if ftype == "year_month":
        if isinstance(value, dict):
            y = value.get("year", "")
            m = str(value.get("month", "")).zfill(2)
            text = f"{m}/{y}"
        else:
            text = str(value) if value is not None else "—"
        lbl = QLabel(text)
        lbl.setObjectName("readonlyValue")
        return lbl

    if ftype == "object":
        gb = QGroupBox(fdef.get("label") or "Details")
        gb.setObjectName("readonlyObjectGroup")
        vlay = QVBoxLayout(gb)
        vlay.setContentsMargins(12, 10, 12, 10)
        vlay.setSpacing(6)
        fields = fdef.get("fields") or []
        val_dict = value if isinstance(value, dict) else {}
        for sub in fields:
            if not isinstance(sub, dict) or not sub.get("name"):
                continue
            sub_name = sub["name"]
            sub_label = sub.get("label") or sub_name
            sub_val = val_dict.get(sub_name)
            row = QHBoxLayout()
            row.addWidget(QLabel(f"<b>{sub_label}:</b>"))
            row.addWidget(_render_value_readonly(sub, sub_val))
            row.addStretch()
            vlay.addLayout(row)
        return gb

    # Default: plain text label
    if value is None:
        text = "—"
    elif isinstance(value, bool):
        text = "Yes" if value else "No"
    else:
        text = str(value).strip() or "—"

    lbl = QLabel(text)
    lbl.setObjectName("readonlyValue")
    lbl.setWordWrap(True)
    return lbl


class _ReadonlyItemView(QFrame):
    """
    Displays one item's fields in read-only form inside a GroupBox.
    An 'Edit' button at the top-right opens the edit overlay for this item only.
    """

    def __init__(
        self,
        section_fields: List[Dict[str, Any]],
        payload: Dict[str, Any],
        title: str,
        allow_multiple: bool,
        on_edit: Callable[[], None],
        palette: QPalette,
    ):
        super().__init__()
        self.section_fields = section_fields
        self.payload = payload
        self.allow_multiple = allow_multiple
        self.on_edit = on_edit
        self._palette = palette

        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setObjectName("readonlyItemFrame")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.group_box = QGroupBox(title)
        self.group_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        gb_layout = QVBoxLayout(self.group_box)
        gb_layout.setContentsMargins(80, 10, 80, 12)
        gb_layout.setSpacing(10)

        # Header row: selected_default badge  +  Edit button
        header = QHBoxLayout()
        header.addStretch()

        if allow_multiple:
            selected = payload.get("selected_default", False)
            badge_text = "Preselected" if selected else "Not preselected"
            badge_color = "#10B981" if selected else "#777777"
            badge = QLabel(badge_text)
            badge.setObjectName("preselectedBadge")
            badge.setStyleSheet(
                f"QLabel#preselectedBadge {{"
                f"  border-radius: 10px; padding: 2px 8px;"
                f"  font-size: 11px; color: #ffffff;"
                f"  background-color: {badge_color};"
                f"}}"
            )
            header.addWidget(badge)
            header.addSpacing(8)

        edit_btn = QPushButton("✎ Edit")
        edit_btn.setObjectName("itemEditBtn")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setFixedHeight(28)
        edit_btn.clicked.connect(self.on_edit)
        header.addWidget(edit_btn)

        gb_layout.addLayout(header)

        # Field grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(8)

        current_row = 0
        current_col = 0
        for fdef in self.section_fields:
            fname = fdef["name"]
            flabel = fdef.get("label") or fname
            is_multi = bool(fdef.get("allow_multiple", False))
            layout_width = str(fdef.get("layout_width", "full"))

            raw_value = payload.get(fname)

            if is_multi:
                # Render as a vertical list
                container = QWidget()
                vlay = QVBoxLayout(container)
                vlay.setContentsMargins(0, 0, 0, 0)
                vlay.setSpacing(4)
                header_lbl = QLabel(f"<b>{flabel}</b>")
                vlay.addWidget(header_lbl)
                entries = raw_value if isinstance(raw_value, list) else ([raw_value] if raw_value else [])
                for entry in entries:
                    entry_lbl = _render_value_readonly(fdef, entry)
                    entry_lbl.setContentsMargins(8, 0, 0, 0)
                    vlay.addWidget(entry_lbl)
                if current_col != 0:
                    current_row += 1
                    current_col = 0
                grid.addWidget(container, current_row, 0, 1, 2)
                current_row += 1

            elif layout_width == "full":
                cell = QWidget()
                cell_lay = QVBoxLayout(cell)
                cell_lay.setContentsMargins(0, 0, 0, 0)
                cell_lay.setSpacing(2)
                cell_lay.addWidget(QLabel(f"<b>{flabel}</b>"))
                cell_lay.addWidget(_render_value_readonly(fdef, raw_value))
                if current_col != 0:
                    current_row += 1
                    current_col = 0
                grid.addWidget(cell, current_row, 0, 1, 2)
                current_row += 1

            else:  # half
                cell = QWidget()
                cell_lay = QVBoxLayout(cell)
                cell_lay.setContentsMargins(0, 0, 0, 0)
                cell_lay.setSpacing(2)
                cell_lay.addWidget(QLabel(f"<b>{flabel}</b>"))
                cell_lay.addWidget(_render_value_readonly(fdef, raw_value))
                grid.addWidget(cell, current_row, current_col)
                current_col += 1
                if current_col >= 2:
                    current_row += 1
                    current_col = 0

        gb_layout.addLayout(grid)
        outer.addWidget(self.group_box)

    def set_title(self, title: str) -> None:
        self.group_box.setTitle(title or "Item")


class _ItemEditOverlay(QWidget):
    """
    Lightweight overlay that lets the user edit a single item.
    Offers three actions:
      • Cancel       — discard changes
      • Save for this CV — saves only to the current CV config
      • Save for all CVs — saves to every CV in the config (or a shared profile)
    """

    def __init__(
        self,
        parent: QWidget,
        palette: QPalette,
        section_def: SectionDef,
        section_cfg: SectionCfg,
        item_index: int,
        config_path: str,
        on_saved: Optional[Callable[[str, Dict[str, Any], bool], None]] = None,
    ):
        super().__init__(parent)

        self.section_def = dict(section_def or {})
        self.section_cfg = dict(section_cfg or {})
        self.item_index = item_index
        self.config_path = config_path
        self.on_saved = on_saved
        self.section_name = (self.section_def.get("name") or "").strip()
        self.allow_multiple = bool(self.section_def.get("allow_multiple", False))

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setObjectName("itemEditOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        window_bg = palette.color(QPalette.ColorRole.Window)
        text_color = palette.color(QPalette.ColorRole.WindowText)
        base_bg = palette.color(QPalette.ColorRole.Base)
        button_bg = palette.color(QPalette.ColorRole.Button)
        highlight = palette.color(QPalette.ColorRole.Highlight)

        dialog_bg = window_bg.lighter(110)
        border_color = window_bg.lighter(140)
        hover_bg = button_bg.lighter(120)

        self.setStyleSheet(
            """
            QWidget#itemEditOverlay { background-color: rgba(0, 0, 0, 180); }
            QFrame#editDialogFrame {
                border-radius: 12px;
                border: 1px solid %(border)s;
                background-color: %(dialog)s;
            }
            QLabel { color: %(text)s; }
            QLineEdit, QTextEdit {
                background-color: %(base)s;
                color: %(text)s;
                border: 1px solid %(border)s;
                border-radius: 6px;
                padding: 6px;
            }
            QLineEdit:focus, QTextEdit:focus { border: 1px solid %(hl)s; }
            QComboBox {
                border: 1px solid %(border)s;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton {
                background-color: %(btn)s;
                color: %(text)s;
                border: 1px solid %(border)s;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: %(hover)s; }
            QPushButton#saveCurrentBtn {
                background-color: %(hl)s;
                border: 1px solid %(hl)s;
            }
            QPushButton#saveCurrentBtn:hover { background-color: %(hl2)s; }
            QPushButton#saveAllBtn {
                background-color: %(hl)s;
                border: 1px solid %(hl)s;
            }
            QPushButton#saveAllBtn:hover { background-color: %(hl2)s; }
            QPushButton#closeBtn {
                background-color: transparent;
                border: none;
                font-size: 18px;
                padding: 4px 8px;
            }
            QPushButton#closeBtn:hover {
                background-color: rgba(128, 128, 128, 50);
                border-radius: 6px;
            }
            QScrollArea { border: none; background-color: transparent; }
            QGroupBox {
                border: 1px solid %(border)s;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
            }
            """
            % {
                "dialog": dialog_bg.name(),
                "border": border_color.name(),
                "text": text_color.name(),
                "base": base_bg.name(),
                "btn": button_bg.name(),
                "hover": hover_bg.name(),
                "hl": highlight.name(),
                "hl2": highlight.darker(110).name(),
            }
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(60, 40, 60, 80)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dialog = QFrame(self)
        self.dialog.setObjectName("editDialogFrame")
        self.dialog.setMinimumSize(300, 300)

        dialog_layout = QVBoxLayout(self.dialog)
        dialog_layout.setContentsMargins(24, 20, 24, 24)
        dialog_layout.setSpacing(16)

        # Title row
        title_row = QHBoxLayout()
        item_label = (
            (self.section_def.get("item_label") or {}).get("singular")
            or self.section_def.get("default_title")
            or self.section_name
            or "Item"
        )
        title_lbl = QLabel(f"Edit {item_label}")
        title_lbl.setStyleSheet("font-weight: 600; font-size: 18px;")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(32, 32)
        title_row.addWidget(close_btn)
        dialog_layout.addLayout(title_row)

        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 8, 0)
        scroll_layout.setSpacing(14)

        # Build the item editor for the targeted item
        items = self.section_cfg.get("items") or []
        if 0 <= item_index < len(items):
            payload = dict(items[item_index])
        else:
            payload = self._make_default_item_payload()

        self._item_editor = _ItemEditor(
            section_fields=self._fields_def(),
            payload=payload,
            palette=palette,
            allow_multiple=self.allow_multiple,
            on_remove=lambda: None,  # remove not applicable here
        )
        scroll_layout.addWidget(self._item_editor)
        scroll_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        dialog_layout.addWidget(scroll_area, 1)

        # Action buttons
        actions = QHBoxLayout()
        actions.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.close)
        cancel_btn.setFixedHeight(36)

        save_current_btn = QPushButton("Save for this CV")
        save_current_btn.setObjectName("saveCurrentBtn")
        save_current_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_current_btn.clicked.connect(self._save_current_cv)
        save_current_btn.setFixedHeight(36)

        save_all_btn = QPushButton("Save for all CVs")
        save_all_btn.setObjectName("saveAllBtn")
        save_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_all_btn.clicked.connect(self._save_all_cvs)
        save_all_btn.setFixedHeight(36)

        actions.addWidget(cancel_btn)
        actions.addSpacing(8)
        actions.addWidget(save_current_btn)
        actions.addSpacing(8)
        actions.addWidget(save_all_btn)
        dialog_layout.addLayout(actions)

        outer.addWidget(self.dialog)
        self.installEventFilter(self)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fields_def(self) -> List[Dict[str, Any]]:
        fields = self.section_def.get("fields") or []
        return [f for f in fields if isinstance(f, dict) and f.get("name")]

    def _make_default_item_payload(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for fdef in self._fields_def():
            fname = fdef["name"]
            is_multi = bool(fdef.get("allow_multiple", False))
            base = _field_default_value(fdef)
            out[fname] = [base] if is_multi else base
        return out

    def _collect_edited_payload(self) -> Dict[str, Any]:
        return self._item_editor.to_payload()

    def _save_current_cv(self) -> None:
        """Persist changes to the current CV only."""
        self._persist(all_cvs=False)

    def _save_all_cvs(self) -> None:
        """Persist changes to every CV entry in the config."""
        self._persist(all_cvs=True)

    def _persist(self, all_cvs: bool) -> None:
        if not self.section_name:
            QMessageBox.warning(self, "Missing section name", "This section has no 'name' in the YAML.")
            return

        new_payload = self._collect_edited_payload()
        full_cfg = load_full_config(self.config_path)

        cv_config = full_cfg.get("cv_config", {})
        sections = cv_config.get("sections", {})
        section_data = dict(sections.get(self.section_name, {}))
        items = list(section_data.get("items") or [])

        # Extend list if needed
        while len(items) <= self.item_index:
            items.append(self._make_default_item_payload())

        if all_cvs:
            # Replace this item across ALL section entries that share the same name.
            # The exact "all CVs" semantics depend on your config schema — here we
            # update the single shared section (the profile store) unconditionally.
            for key in sections:
                sec = dict(sections[key])
                if key == self.section_name:
                    sec_items = list(sec.get("items") or [])
                    while len(sec_items) <= self.item_index:
                        sec_items.append(self._make_default_item_payload())
                    sec_items[self.item_index] = new_payload
                    sec["items"] = sec_items
                    sections[key] = sec
        else:
            items[self.item_index] = new_payload
            section_data["items"] = items
            sections[self.section_name] = section_data

        cv_config["sections"] = sections
        full_cfg["cv_config"] = cv_config
        save_full_config(self.config_path, full_cfg)

        if self.on_saved:
            self.on_saved(self.section_name, new_payload, all_cvs)

        self.close()

    # ------------------------------------------------------------------
    # Geometry / event handling
    # ------------------------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        self._fit_to_parent()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_to_parent()

    def _fit_to_parent(self):
        p = self.parentWidget()
        if p is not None:
            self.setGeometry(p.rect())

    def eventFilter(self, obj, event):
        if obj is self and event.type() == QEvent.Type.MouseButtonPress:
            if not self.dialog.geometry().contains(event.position().toPoint()):
                self.close()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        super().closeEvent(event)
        parent = self.parentWidget()
        if parent and hasattr(parent, "_item_overlay") and parent._item_overlay is self:
            parent._item_overlay = None


class _AddItemOverlay(QWidget):
    """
    Minimal overlay for adding a *new* item to the section.
    Offers Cancel / Save for this CV / Save for all CVs.
    """

    def __init__(
        self,
        parent: QWidget,
        palette: QPalette,
        section_def: SectionDef,
        section_cfg: SectionCfg,
        config_path: str,
        on_saved: Optional[Callable[[str, Dict[str, Any], bool], None]] = None,
    ):
        super().__init__(parent)

        self.section_def = dict(section_def or {})
        self.section_cfg = dict(section_cfg or {})
        self.config_path = config_path
        self.on_saved = on_saved
        self.section_name = (self.section_def.get("name") or "").strip()
        self.allow_multiple = bool(self.section_def.get("allow_multiple", False))

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setObjectName("addItemOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        window_bg = palette.color(QPalette.ColorRole.Window)
        text_color = palette.color(QPalette.ColorRole.WindowText)
        base_bg = palette.color(QPalette.ColorRole.Base)
        button_bg = palette.color(QPalette.ColorRole.Button)
        highlight = palette.color(QPalette.ColorRole.Highlight)
        dialog_bg = window_bg.lighter(110)
        border_color = window_bg.lighter(140)
        hover_bg = button_bg.lighter(120)

        self.setStyleSheet(
            """
            QWidget#addItemOverlay { background-color: rgba(0, 0, 0, 180); }
            QFrame#addDialogFrame {
                border-radius: 12px;
                border: 1px solid %(border)s;
                background-color: %(dialog)s;
            }
            QLabel { color: %(text)s; }
            QLineEdit, QTextEdit {
                background-color: %(base)s;
                color: %(text)s;
                border: 1px solid %(border)s;
                border-radius: 6px;
                padding: 6px;
            }
            QLineEdit:focus, QTextEdit:focus { border: 1px solid %(hl)s; }
            QComboBox { border: 1px solid %(border)s; border-radius: 6px; padding: 6px; }
            QPushButton {
                background-color: %(btn)s;
                color: %(text)s;
                border: 1px solid %(border)s;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: %(hover)s; }
            QPushButton#saveCurrentBtn { background-color: %(hl)s; border: 1px solid %(hl)s; }
            QPushButton#saveCurrentBtn:hover { background-color: %(hl2)s; }
            QPushButton#saveAllBtn { background-color: %(hl)s; border: 1px solid %(hl)s; }
            QPushButton#saveAllBtn:hover { background-color: %(hl2)s; }
            QPushButton#closeBtn {
                background-color: transparent; border: none;
                font-size: 18px; padding: 4px 8px;
            }
            QPushButton#closeBtn:hover { background-color: rgba(128,128,128,50); border-radius: 6px; }
            QScrollArea { border: none; background-color: transparent; }
            QGroupBox { border: 1px solid %(border)s; border-radius: 8px; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; }
            """
            % {
                "dialog": dialog_bg.name(),
                "border": border_color.name(),
                "text": text_color.name(),
                "base": base_bg.name(),
                "btn": button_bg.name(),
                "hover": hover_bg.name(),
                "hl": highlight.name(),
                "hl2": highlight.darker(110).name(),
            }
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(60, 40, 60, 80)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dialog = QFrame(self)
        self.dialog.setObjectName("addDialogFrame")
        self.dialog.setMinimumSize(300, 300)

        dialog_layout = QVBoxLayout(self.dialog)
        dialog_layout.setContentsMargins(24, 20, 24, 24)
        dialog_layout.setSpacing(16)

        singular = (self.section_def.get("item_label") or {}).get("singular") or "Item"
        title_row = QHBoxLayout()
        title_lbl = QLabel(f"Add {singular}")
        title_lbl.setStyleSheet("font-weight: 600; font-size: 18px;")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(32, 32)
        title_row.addWidget(close_btn)
        dialog_layout.addLayout(title_row)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 8, 0)
        scroll_layout.setSpacing(14)

        self._item_editor = _ItemEditor(
            section_fields=self._fields_def(),
            payload=self._make_default_item_payload(),
            palette=palette,
            allow_multiple=self.allow_multiple,
            on_remove=lambda: None,
        )
        scroll_layout.addWidget(self._item_editor)
        scroll_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        dialog_layout.addWidget(scroll_area, 1)

        actions = QHBoxLayout()
        actions.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.close)
        cancel_btn.setFixedHeight(36)
        save_current_btn = QPushButton("Save for this CV")
        save_current_btn.setObjectName("saveCurrentBtn")
        save_current_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_current_btn.clicked.connect(self._save_current_cv)
        save_current_btn.setFixedHeight(36)
        save_all_btn = QPushButton("Save for all CVs")
        save_all_btn.setObjectName("saveAllBtn")
        save_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_all_btn.clicked.connect(self._save_all_cvs)
        save_all_btn.setFixedHeight(36)
        actions.addWidget(cancel_btn)
        actions.addSpacing(8)
        actions.addWidget(save_current_btn)
        actions.addSpacing(8)
        actions.addWidget(save_all_btn)
        dialog_layout.addLayout(actions)

        outer.addWidget(self.dialog)
        self.installEventFilter(self)

    def _fields_def(self) -> List[Dict[str, Any]]:
        fields = self.section_def.get("fields") or []
        return [f for f in fields if isinstance(f, dict) and f.get("name")]

    def _make_default_item_payload(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for fdef in self._fields_def():
            fname = fdef["name"]
            is_multi = bool(fdef.get("allow_multiple", False))
            base = _field_default_value(fdef)
            out[fname] = [base] if is_multi else base
        return out

    def _save_current_cv(self):
        self._persist(all_cvs=False)

    def _save_all_cvs(self):
        self._persist(all_cvs=True)

    def _persist(self, all_cvs: bool):
        if not self.section_name:
            QMessageBox.warning(self, "Missing section name", "This section has no 'name' in the YAML.")
            return

        new_item = self._item_editor.to_payload()
        full_cfg = load_full_config(self.config_path)
        cv_config = full_cfg.get("cv_config", {})
        sections = cv_config.get("sections", {})
        section_data = dict(sections.get(self.section_name, {}))
        items = list(section_data.get("items") or [])
        items.append(new_item)

        if all_cvs:
            for key in sections:
                if key == self.section_name:
                    sec = dict(sections[key])
                    sec_items = list(sec.get("items") or [])
                    sec_items.append(new_item)
                    sec["items"] = sec_items
                    sections[key] = sec
        else:
            section_data["items"] = items
            sections[self.section_name] = section_data

        cv_config["sections"] = sections
        full_cfg["cv_config"] = cv_config
        save_full_config(self.config_path, full_cfg)

        if self.on_saved:
            self.on_saved(self.section_name, new_item, all_cvs)

        self.close()

    def showEvent(self, event):
        super().showEvent(event)
        self._fit_to_parent()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_to_parent()

    def _fit_to_parent(self):
        p = self.parentWidget()
        if p is not None:
            self.setGeometry(p.rect())

    def eventFilter(self, obj, event):
        if obj is self and event.type() == QEvent.Type.MouseButtonPress:
            if not self.dialog.geometry().contains(event.position().toPoint()):
                self.close()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        super().closeEvent(event)
        parent = self.parentWidget()
        if parent and hasattr(parent, "_add_overlay") and parent._add_overlay is self:
            parent._add_overlay = None


class SectionSelectionPage(QWidget):
    """
    Read-only display page for a single section's saved data.

    Shows each item with all its fields in read-only form.
    An 'Edit' button on each item opens _ItemEditOverlay.
    An 'Add <item>' button (when allow_multiple) opens _AddItemOverlay.
    A settings gear button opens the full SectionSettingsOverlay.

    Constructor mirrors SectionSettingsOverlay for easy drop-in usage:

        page = SectionSelectionPage(
            parent=...,
            palette=app.palette(),
            section_def=section_def,   # dict from section_types.yml
            config_path=str(paths["config"]),
        )
    """

    def __init__(
        self,
        palette: QPalette,
        section_def: SectionDef,
        config_path: str,
        parent: QWidget | None = None,
        on_item_saved: Optional[Callable[[str, Dict[str, Any], bool], None]] = None,
    ):
        super().__init__(parent)

        self.palette_ref = palette
        self.section_def = dict(section_def or {})
        self.config_path = config_path
        self.on_item_saved = on_item_saved

        self.section_name = (self.section_def.get("name") or "").strip()
        self.allow_multiple = bool(self.section_def.get("allow_multiple", False))

        self._item_overlay: Optional[_ItemEditOverlay] = None
        self._add_overlay: Optional[_AddItemOverlay] = None
        self._settings_overlay: Optional[SectionSettingsOverlay] = None

        self._init_ui()
        self._load_and_render()

    # ------------------------------------------------------------------
    # UI skeleton (built once)
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.frame = QFrame(self)
        self.frame.setObjectName("sectionSelectionFrame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        root_layout.addWidget(self.frame)

        self.main_layout = QVBoxLayout(self.frame)
        self.main_layout.setContentsMargins(16, 14, 16, 16)
        self.main_layout.setSpacing(12)

        # Header
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        self._title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self._title_label.setFont(title_font)
        header_row.addWidget(self._title_label, stretch=1)

        self._status_badge = QLabel()
        self._status_badge.setObjectName("sectionStatusBadge")
        header_row.addWidget(self._status_badge, stretch=0)

        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setObjectName("settingsBtn")
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setFixedHeight(30)
        settings_btn.clicked.connect(self._open_settings_overlay)
        header_row.addWidget(settings_btn)

        self.main_layout.addLayout(header_row)

        # Sub-header (description)
        self._desc_label = QLabel()
        self._desc_label.setWordWrap(True)
        self._desc_label.setObjectName("sectionDescLabel")
        self.main_layout.addWidget(self._desc_label)

        # Scrollable items area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setObjectName("itemsScrollArea")

        self._scroll_content = QWidget()
        self._items_layout = QVBoxLayout(self._scroll_content)
        self._items_layout.setContentsMargins(0, 0, 8, 0)
        self._items_layout.setSpacing(12)
        self._items_layout.addStretch(1)

        scroll_area.setWidget(self._scroll_content)
        self.main_layout.addWidget(scroll_area, stretch=1)

        # Footer: "Add item" button
        footer_row = QHBoxLayout()
        footer_row.addStretch()

        self._add_btn = QPushButton()
        self._add_btn.setObjectName("addItemBtn")
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.setFixedHeight(34)
        self._add_btn.clicked.connect(self._open_add_overlay)
        footer_row.addWidget(self._add_btn)
        footer_row.addStretch()
        self.main_layout.addLayout(footer_row)

        self._apply_stylesheet()

    def _apply_stylesheet(self) -> None:
        p = self.palette_ref
        highlight = p.color(QPalette.ColorRole.Highlight)
        border_color = p.color(QPalette.ColorRole.Window).lighter(140)

        self.setStyleSheet(
            f"""
            QFrame#sectionSelectionFrame {{
                border: 1px solid {border_color.name()};
                border-radius: 8px;
            }}
            QPushButton#settingsBtn {{
                border: 1px solid {border_color.name()};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QPushButton#addItemBtn {{
                background-color: {highlight.name()};
                border: 1px solid {highlight.name()};
                border-radius: 6px;
                padding: 4px 16px;
                font-size: 13px;
                color: white;
            }}
            QPushButton#addItemBtn:hover {{
                background-color: {highlight.darker(110).name()};
            }}
            QPushButton#itemEditBtn {{
                border: 1px solid {border_color.name()};
                border-radius: 6px;
                padding: 2px 10px;
                font-size: 12px;
            }}
            QPushButton#itemEditBtn:hover {{
                background-color: {highlight.name()};
                color: white;
            }}
            QLabel#readonlyValue {{
                padding: 2px 0px;
            }}
            QLabel#sectionDescLabel {{
                color: gray;
                font-size: 11px;
            }}
            QScrollArea#itemsScrollArea {{
                border: none;
                background: transparent;
            }}
            """
        )

    # ------------------------------------------------------------------
    # Data loading & rendering
    # ------------------------------------------------------------------

    def _load_section_cfg(self) -> SectionCfg:
        cv_cfg = load_cv_config(self.config_path)
        return cv_cfg.get("sections", {}).get(self.section_name, {})

    def _load_and_render(self) -> None:
        section_cfg = self._load_section_cfg()
        self._render(section_cfg)

    def _render(self, section_cfg: SectionCfg) -> None:
        # Header info
        default_title = self.section_def.get("default_title") or self.section_name.title()
        title_override = section_cfg.get("title_override")
        title = title_override or default_title
        self._title_label.setText(title)

        enabled = section_cfg.get("enabled", True)
        status_text = "Enabled" if enabled else "Hidden"
        badge_color = "#10B981" if enabled else "#777777"
        self._status_badge.setText(status_text)
        self._status_badge.setStyleSheet(
            f"border-radius: 10px; padding: 2px 8px; font-size: 11px;"
            f" color: #ffffff; background-color: {badge_color};"
        )

        desc = (self.section_def.get("description") or "").strip()
        self._desc_label.setText(desc)
        self._desc_label.setVisible(bool(desc))

        # Add-item button label
        singular = (self.section_def.get("item_label") or {}).get("singular") or "Item"
        # plural = (self.section_def.get("item_label") or {}).get("plural") or "Items"
        self._add_btn.setText(f"＋ Add {singular}")
        self._add_btn.setVisible(self.allow_multiple)

        # Clear existing item views (remove all widgets except the trailing stretch)
        while self._items_layout.count() > 1:
            item = self._items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Rebuild item views
        items = section_cfg.get("items") or []
        if not items:
            items = [{}]
        if not self.allow_multiple:
            items = items[:1]

        fields_def = [
            f for f in (self.section_def.get("fields") or [])
            if isinstance(f, dict) and f.get("name")
        ]

        for idx, payload in enumerate(items):
            if len(items) > 1:
                item_title = f"{singular} {idx + 1}"
            else:
                item_title = singular

            view = _ReadonlyItemView(
                section_fields=fields_def,
                payload=payload,
                title=item_title,
                allow_multiple=self.allow_multiple,
                on_edit=lambda i=idx: self._open_edit_overlay(i),
                palette=self.palette_ref,
            )
            view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            # Insert before the trailing stretch
            self._items_layout.insertWidget(self._items_layout.count() - 1, view)

    # ------------------------------------------------------------------
    # Overlay launchers
    # ------------------------------------------------------------------

    def _open_edit_overlay(self, item_index: int) -> None:
        if self._item_overlay is not None:
            self._item_overlay.deleteLater()
            self._item_overlay = None

        section_cfg = self._load_section_cfg()

        self._item_overlay = _ItemEditOverlay(
            parent=self,
            palette=self.palette_ref,
            section_def=self.section_def,
            section_cfg=section_cfg,
            item_index=item_index,
            config_path=self.config_path,
            on_saved=self._on_item_saved,
        )
        self._item_overlay.show()
        self._item_overlay.raise_()

    def _open_add_overlay(self) -> None:
        if self._add_overlay is not None:
            self._add_overlay.deleteLater()
            self._add_overlay = None

        section_cfg = self._load_section_cfg()

        self._add_overlay = _AddItemOverlay(
            parent=self,
            palette=self.palette_ref,
            section_def=self.section_def,
            section_cfg=section_cfg,
            config_path=self.config_path,
            on_saved=self._on_item_saved,
        )
        self._add_overlay.show()
        self._add_overlay.raise_()

    def _open_settings_overlay(self) -> None:
        if self._settings_overlay is not None:
            self._settings_overlay.deleteLater()
            self._settings_overlay = None

        section_cfg = self._load_section_cfg()

        self._settings_overlay = SectionSettingsOverlay(
            parent=self,
            palette=self.palette_ref,
            section_def=self.section_def,
            section_cfg=section_cfg,
            config_path=self.config_path,
            on_saved=self._on_settings_saved,
        )
        self._settings_overlay.show()
        self._settings_overlay.raise_()

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_item_saved(self, section_name: str, payload: Dict[str, Any], all_cvs: bool) -> None:
        self._load_and_render()
        if self.on_item_saved:
            self.on_item_saved(section_name, payload, all_cvs)

    def _on_settings_saved(self, section_name: str, section_payload: Dict[str, Any]) -> None:
        self._load_and_render()

    # ------------------------------------------------------------------
    # Resize: keep overlays in sync
    # ------------------------------------------------------------------

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for overlay in (self._item_overlay, self._add_overlay, self._settings_overlay):
            if overlay is not None and overlay.isVisible():
                overlay.setGeometry(self.rect())


class TargetApplicationPage(QWidget):
    """Page to select the targeted job application for the CV"""

    ROWS_COMPLETER = 2

    TABLE_HEADERS = ["Date applied", "Position", "Company", "Location", "Status", "Source"]
    TABLE_COLS = ["date_applied", "position", "company", "location", "status", "source"]

    def __init__(
        self,
        db: JobDatabase,
        palette: QPalette,
        section_name: str,
        section_label: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.db = db
        self.palette = palette
        self.section_name = section_name
        self.section_label = section_label

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # ── Row 1: Search bar ───────────────────────────────────────────────
        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(12)

        self.searchbar = QLineEdit()
        self.searchbar.setObjectName("searchBar")
        self.searchbar.setPlaceholderText(
            "Search jobs by company, position, or location..."
        )
        self.searchbar.setClearButtonEnabled(True)
        self.searchbar.textChanged.connect(self.update_jobs_displayed)
        self.searchbar.addAction(
            SEARCH_ICON,
            QLineEdit.ActionPosition.LeadingPosition,
        )

        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.searchbar.setCompleter(self.completer)
        popup = self.completer.popup()
        popup.setObjectName("completerPopup")
        popup.setUniformItemSizes(True)
        popup.setMaximumHeight(
            (self.searchbar.fontMetrics().height() + 4) * self.ROWS_COMPLETER + 2
        )

        search_row.addWidget(self.searchbar, stretch=1)
        layout.addLayout(search_row)

        # ── Row 2: Filter bar ───────────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(8)

        filter_icon_label = QLabel()
        filter_icon_label.setPixmap(FILTER_ICON.pixmap(16, 16))
        filter_icon_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        )
        filter_by_label = QLabel("Filter by:")
        filter_by_label.setObjectName("filterByLabel")
        filter_by_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        filter_row.addWidget(filter_icon_label)
        filter_row.addWidget(filter_by_label)

        status_label = QLabel("Status")
        status_label.setObjectName("filterLabel")
        self.status_filter = NoScrollComboBox()
        self.status_filter.setObjectName("filterCombo")
        self.status_filter.addItem("Any")
        self.status_filter.addItems(STATUS_OPTIONS)
        self.status_filter.setMinimumHeight(30)
        self.status_filter.currentTextChanged.connect(
            lambda _: self.update_jobs_displayed(self.searchbar.text())
        )
        filter_row.addWidget(status_label)
        filter_row.addWidget(self.status_filter)

        filter_row.addWidget(self._make_separator())

        job_type_label = QLabel("Job type")
        job_type_label.setObjectName("filterLabel")
        self.job_type_filter = NoScrollComboBox()
        self.job_type_filter.setObjectName("filterCombo")
        self.job_type_filter.addItem("Any")
        self.job_type_filter.addItems(JOB_TYPE_OPTIONS)
        self.job_type_filter.setMinimumHeight(30)
        self.job_type_filter.currentTextChanged.connect(
            lambda _: self.update_jobs_displayed(self.searchbar.text())
        )
        filter_row.addWidget(job_type_label)
        filter_row.addWidget(self.job_type_filter)

        filter_row.addWidget(self._make_separator())

        arrangement_label = QLabel("Arrangement")
        arrangement_label.setObjectName("filterLabel")
        self.arrangement_filter = NoScrollComboBox()
        self.arrangement_filter.setObjectName("filterCombo")
        self.arrangement_filter.addItem("Any")
        self.arrangement_filter.addItems(WORK_ARRANGEMENT_OPTIONS)
        self.arrangement_filter.setMinimumHeight(30)
        self.arrangement_filter.currentTextChanged.connect(
            lambda _: self.update_jobs_displayed(self.searchbar.text())
        )
        filter_row.addWidget(arrangement_label)
        filter_row.addWidget(self.arrangement_filter)

        filter_row.addWidget(self._make_separator())

        date_label = QLabel("Applied")
        date_label.setObjectName("filterLabel")
        date_from_label = QLabel("from")
        date_from_label.setObjectName("filterLabel")
        date_to_label = QLabel("to")
        date_to_label.setObjectName("filterLabel")

        today = QDate.currentDate()

        self.date_from_filter = NoScrollDateEdit()
        self.date_from_filter.setObjectName("filterDate")
        self.date_from_filter.setMinimumHeight(30)
        self.date_from_filter.setSpecialValueText(" ")
        self.date_from_filter.setMinimumDate(QDate(2000, 1, 1))
        self.date_from_filter.setMaximumDate(today)
        self.date_from_filter.setDate(QDate(2000, 1, 1))
        self.date_from_filter.dateChanged.connect(
            lambda _: self.update_jobs_displayed(self.searchbar.text())
        )

        self.date_to_filter = NoScrollDateEdit()
        self.date_to_filter.setObjectName("filterDate")
        self.date_to_filter.setMinimumHeight(30)
        self.date_to_filter.setSpecialValueText(" ")
        self.date_to_filter.setMinimumDate(QDate(2000, 1, 1))
        self.date_to_filter.setMaximumDate(today.addYears(1))
        self.date_to_filter.setDate(today)
        self.date_to_filter.dateChanged.connect(
            lambda _: self.update_jobs_displayed(self.searchbar.text())
        )

        filter_row.addWidget(date_label)
        filter_row.addWidget(date_from_label)
        filter_row.addWidget(self.date_from_filter)
        filter_row.addWidget(date_to_label)
        filter_row.addWidget(self.date_to_filter)

        filter_row.addStretch(1)
        filter_row.addWidget(self._make_separator())

        sort_label = QLabel("Order by:")
        sort_label.setObjectName("filterByLabel")
        sort_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.sort_combo = NoScrollComboBox()
        self.sort_combo.setObjectName("filterCombo")
        self.sort_combo.addItems([
            "Date applied \u2193",
            "Date applied \u2191",
            "Last update \u2193",
            "Last update \u2191",
        ])
        self.sort_combo.setMinimumHeight(30)
        self.sort_combo.currentTextChanged.connect(
            lambda _: self._sort_table()
        )
        filter_row.addWidget(sort_label)
        filter_row.addWidget(self.sort_combo)

        layout.addLayout(filter_row)

        # ── Job Table ───────────────────────────────────────────────────────
        self.job_table = QTableWidget()
        self.job_table.setColumnCount(len(self.TABLE_HEADERS))
        self.job_table.setHorizontalHeaderLabels(self.TABLE_HEADERS)
        self.job_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.job_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.job_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.job_table.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self.job_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.job_table.verticalHeader().setVisible(False)
        self.job_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.job_table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.job_table.setWordWrap(False)

        fm = self.job_table.fontMetrics()
        padding = 24

        self.job_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.job_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.job_table.setColumnWidth(0, fm.horizontalAdvance("DD/MM/YYYY") + padding)
        self.job_table.setColumnWidth(4, fm.horizontalAdvance("Interview Scheduled") + padding)
        

        layout.addWidget(self.job_table)

        self.query_all_job_apps()
        self.populate_job_table()

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _make_separator() -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setObjectName("filterSeparator")
        sep.setFixedWidth(1)
        sep.setMinimumHeight(20)
        return sep

    # ── Data / population ────────────────────────────────────────────────────

    def populate_job_table(self):
        self.job_table.setRowCount(0)

        for job in self.job_applications:
            row = self.job_table.rowCount()
            self.job_table.insertRow(row)

            for col, key in enumerate(self.TABLE_COLS):
                item = QTableWidgetItem(job.get(key) or "")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:
                    # Anchor the job dict here so get_selected_job can retrieve it
                    item.setData(Qt.ItemDataRole.UserRole, job)
                self.job_table.setItem(row, col, item)

    def query_all_job_apps(self):
        """Fetch all job applications from the database into self.job_applications."""
        rows = self.db.get_all_jobs()

        self.job_applications = []
        for r in rows:
            self.job_applications.append({
                "id": r[0],
                "company": r[1],
                "company_website": r[2],
                "position": r[3],
                "status": r[4],
                "location": r[5],
                "source": r[6],
                "job_type": r[7],
                "date_applied": r[8],
                "contact_name": r[9],
                "contact_email": r[10],
                "salary_range": r[11],
                "work_arrangement": r[12],
                "office_days": r[13],
                "job_url": r[14],
                "job_description": r[15],
                "notes": r[16],
                "last_update": r[19],
            })

        self.job_companies = [j["company"] for j in self.job_applications]
        self.job_positions = [j["position"] for j in self.job_applications]
        self.job_locations = [j["location"] for j in self.job_applications if j.get("location")]
        self.completer_hints = self.job_companies + self.job_positions + self.job_locations
        self.update_completer_hints(self.completer_hints)

    # ── Filtering / sorting ──────────────────────────────────────────────────

    def update_jobs_displayed(self, text):
        t = (text or "").lower().strip()
        selected_status = (self.status_filter.currentText() or "").strip()
        selected_job_type = (self.job_type_filter.currentText() or "").strip()
        selected_arrangement = (self.arrangement_filter.currentText() or "").strip()

        date_from = self.date_from_filter.date()
        date_to = self.date_to_filter.date()
        no_lower_bound = (date_from == QDate(2000, 1, 1))

        for row in range(self.job_table.rowCount()):
            job = self.job_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

            matches_text = (
                (not t)
                or t in (job.get("company") or "").lower()
                or t in (job.get("position") or "").lower()
                or t in (job.get("location") or "").lower()
            )

            matches_status = (
                selected_status == "Any"
                or job["status"].strip() == selected_status
            )

            matches_job_type = (
                selected_job_type == "Any"
                or (job.get("job_type") or "").strip() == selected_job_type
            )

            matches_arrangement = (
                selected_arrangement == "Any"
                or (job.get("work_arrangement") or "").strip() == selected_arrangement
            )

            matches_date = True
            if job.get("date_applied"):
                card_date = QDate.fromString(job["date_applied"], Qt.DateFormat.ISODate)
                if card_date.isValid():
                    if not no_lower_bound and card_date < date_from:
                        matches_date = False
                    if card_date > date_to:
                        matches_date = False

            self.job_table.setRowHidden(
                row,
                not (matches_text and matches_status and matches_job_type
                     and matches_arrangement and matches_date),
            )

    # ── Selection ────────────────────────────────────────────────────────────

    def get_selected_job(self):
        selected = self.job_table.selectedItems()
        if not selected:
            return None
        return self.job_table.item(selected[0].row(), 0).data(Qt.ItemDataRole.UserRole)

    # ── Completer ────────────────────────────────────────────────────────────

    def update_completer_hints(self, hints: list[str]):
        self.completer.setModel(QStringListModel(hints))

    def _sort_table(self):
        text = self.sort_combo.currentText()

        def key_fn(job):
            if "Date applied" in text:
                return job.get("date_applied") or ""
            else:
                return job.get("last_update") or ""

        reverse = "\u2193" in text

        self.job_applications.sort(key=key_fn, reverse=reverse)
        self.populate_job_table()
        self.update_jobs_displayed(self.searchbar.text())

    def refresh(self):
        """Re-fetch all jobs from the database and repopulate the table."""
        self.query_all_job_apps()
        self.populate_job_table()
        self.update_jobs_displayed(self.searchbar.text())

    def showEvent(self, event):
        super().showEvent(event)
        # widget just became visible
        self.refresh()

class CVEditorContainer(QWidget):
    """Container for CV editor with persistent top navigation"""
    
    back_to_list = pyqtSignal()
    
    def __init__(
        self,
        db: JobDatabase,
        palette: QPalette,
        paths: Dict[str, Path],
        parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.db = db
        self.palette = palette
        self.paths = paths
        self.section_defs = []
        self.cv_data = {}

        self._load_sections()
        self._build_ui()
        
    def _load_sections(self) -> None:
        """Load section definitions in the correct order"""
        all_defs = load_section_names_from_yaml()
        cv_cfg = load_cv_config(self.paths.get("config"))
        order = cv_cfg.get("section_order")
        
        if order:
            defs_by_name = {d["name"]: d for d in all_defs}
            self.section_defs = [defs_by_name[n] for n in order if n in defs_by_name]
        else:
            self.section_defs = all_defs

        self.user_profile = cv_cfg.get("sections", {})
        self._section_defs_by_name = {d["name"]: d for d in self.section_defs}
        
    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top navigation (always visible)
        self.top_nav = CVTopNavigator(self.section_defs, self)
        self.top_nav.back_clicked.connect(self.back_to_list.emit)
        self.top_nav.section_selected.connect(self._show_section)
        
        main_layout.addWidget(self.top_nav)
        
        # Content area (stacked widget for different sections)
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        # Create all section pages
        self.section_pages: Dict[str, QWidget] = {}
        
        # Add Target Application page
        self._create_target_app_page("target_application", "Target Application")
        
        # Add section pages (only real YAML-defined sections)
        for section_def in self.section_defs:
            section_name = section_def.get("name", "")
            self._create_section_page(section_name)
        
        # Add special pages (not backed by section defs)
        self._create_placeholder_page("reorder_sections", "Reorder Sections")
        self._create_placeholder_page("preview", "Preview CV")
        
        # Show first section by default
        self._show_section("target_application")

    def _create_target_app_page(self, section_name: str, section_label: str) -> None:
        """Create and add a target_application page to the stack"""
        page = TargetApplicationPage(
            self.db,
            self.palette,
            section_name, 
            section_label, 
            self)
        self.content_stack.addWidget(page)
        self.section_pages[section_name] = page
        
    def _create_section_page(self, section_name: str) -> None:
        """Create and add a SectionSelectionPage for a YAML-defined section."""
        section_def = self._section_defs_by_name.get(section_name)
        if section_def is None:
            raise ValueError(
                f"_create_section_page: no section_def found for {section_name!r}. "
                f"Ensure _load_sections() is called before _create_section_page()."
            )
        page = SectionSelectionPage(
            palette=self.palette,
            section_def=section_def,
            config_path=str(self.paths.get("config")),
            parent=self,
        )
        self.content_stack.addWidget(page)
        self.section_pages[section_name] = page

    def _create_placeholder_page(self, section_name: str, section_label: str) -> None:
        page = SectionPlaceholderPage(section_name, section_label, self)
        self.content_stack.addWidget(page)
        self.section_pages[section_name] = page
        
    def _show_section(self, section_name: str) -> None:
        """Show a specific section page"""
        if section_name in self.section_pages:
            self.content_stack.setCurrentWidget(self.section_pages[section_name])
            self.top_nav.set_active_section(section_name)

    def set_cv_information(self, cv:Path | None = None) -> None:
        """Retrieves information from a cv json and sets it for the cv editor instance"""
        if cv is None:
            return


class CVBuilderPage(QWidget):
    
    def __init__(
        self, 
        db: JobDatabase, 
        palette: QPalette, 
        paths: Dict[str, Path],
        parent: QWidget | None = None,
        ):
        super().__init__(parent)
        self.db = db
        self.palette = palette
        self.paths = paths

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.subpages = QStackedWidget()
        self.layout.addWidget(self.subpages)

        # Main list page
        self.main_page = CVListPage(db, palette, paths, self)
        self.main_page.create_cv_clicked.connect(self._show_cv_editor)
        
        # CV editor container with persistent navigation
        self.editor_container = CVEditorContainer(db, palette, paths, self)
        self.editor_container.back_to_list.connect(self._show_main_list)
        
        self.subpages.addWidget(self.main_page)
        self.subpages.addWidget(self.editor_container)
    
    def _show_main_list(self) -> None:
        """Show the main CV list page"""
        self.subpages.setCurrentWidget(self.main_page)
    
    def _show_cv_editor(self, cv:Path | None = None) -> None:
        """Show the CV editor with navigation"""
        self.editor_container.set_cv_information(cv)
        self.subpages.setCurrentWidget(self.editor_container)