from __future__ import annotations

from pathlib import Path

from importlib import resources
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import yaml
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QPalette, QFont, QIcon, QIntValidator
from PyQt6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QPushButton,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QGroupBox,
    QMessageBox,
)

from myapp.QToggle import QToggle
from myapp.utils import (
    load_cv_config, 
    load_full_config, 
    save_full_config,
    today_year_month,
)

from myapp.utils import NoScrollComboBox

# TODO: Do a fail safe if the yml files are wrong.
# TODO: Decide whether "Profile" is an appropriate name

STATUS_COLORS = {
    "Enabled": "#10B981",
    "Hidden": "#777777",
}

EDIT_ICON = QIcon.fromTheme("document-edit")

SectionDef = Dict[str, Any]
SectionCfg = Dict[str, Any]


def _field_default_value(field_def: Dict[str, Any]) -> Any:
    ftype = field_def.get("type")

    # default_value from YAML if present and non-empty
    if "default_value" in field_def:
        dv = field_def.get("default_value")
        if dv is not None and str(dv).strip() != "":
            return dv

    if ftype == "year_month":
        y, m = today_year_month()
        return {"year": y, "month": m}

    if ftype == "enum":
        opts = field_def.get("options") or []
        return opts[0] if isinstance(opts, list) and opts else ""

    if ftype in ("string", "multiline"):
        return ""

    if ftype == "number":
        return 0

    if ftype == "object":
        # build dict for nested fields
        out = {}
        for sub in (field_def.get("fields") or []):
            if isinstance(sub, dict) and sub.get("name"):
                out[sub["name"]] = _field_default_value(sub)
        return out

    return ""


class SectionSettingsOverlay(QWidget):
    """
    Dynamic overlay to edit one section config (state + items + per-field selected_default).

    Persist behaviour:
      - Reads full config from config_path.
      - Overwrites only full_cfg["sections"][section_name] with the edited section payload.
      - Writes the full file back.
    """

    def __init__(
        self,
        parent: QWidget,
        palette: QPalette,
        section_def: SectionDef,
        section_cfg: SectionCfg,
        config_path: str,
        on_saved: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        super().__init__(parent)

        self.section_def = dict(section_def or {})
        self.section_cfg = dict(section_cfg or {})
        self.config_path = config_path
        self.on_saved = on_saved

        self.section_name = (self.section_def.get("name") or "").strip()
        self.allow_multiple = bool(self.section_def.get("allow_multiple", False))
        self.select_multiple = bool(self.section_def.get("select_multiple", True))

        self._item_widgets: List["_ItemEditor"] = []

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setObjectName("overlay")
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
            QWidget#overlay { background-color: rgba(0, 0, 0, 180); }
            QFrame#dialogFrame {
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
                background-color: %(base)s;
                color: %(text)s;
                border: 1px solid %(border)s;
                border-radius: 6px;
                padding: 6px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: %(base)s;
                color: %(text)s;
                selection-background-color: %(hl)s;
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
            QPushButton#saveBtn {
                background-color: %(hl)s;
                border: 1px solid %(hl)s;
            }
            QPushButton#saveBtn:hover { background-color: %(hl2)s; }
            QPushButton#addBtn {
                background-color: %(hl)s;
                border: 1px solid %(hl)s;
            }
            QPushButton#addBtn:hover { background-color: %(hl2)s; }
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
        self.dialog.setObjectName("dialogFrame")
        self.dialog.setMinimumSize(300, 520)

        dialog_layout = QVBoxLayout(self.dialog)
        dialog_layout.setContentsMargins(24, 20, 24, 24)
        dialog_layout.setSpacing(16)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel(self.section_def.get("default_title") or self.section_name or "Section Settings")
        title.setStyleSheet("font-weight: 600; font-size: 18px;")
        title_row.addWidget(title)
        title_row.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(32, 32)
        title_row.addWidget(close_btn)
        dialog_layout.addLayout(title_row)

        # Optional description
        desc = (self.section_def.get("description") or "").strip()
        if desc:
            desc_lbl = QLabel(desc)
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet("opacity: 0.9;")
            dialog_layout.addWidget(desc_lbl)

        # Scroll body
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 8, 0)
        self.scroll_layout.setSpacing(14)

        # Section state selector
        self.scroll_layout.addWidget(self._build_section_visibility_block())

        # Items block
        self.items_container = QVBoxLayout()
        self.items_container.setSpacing(12)
        self.scroll_layout.addLayout(self.items_container)

        # Add item button (only if allow_multiple)
        if self.allow_multiple:
            add_item_row = QHBoxLayout()
            add_item_row.addStretch()
            self.add_item_btn = QPushButton("＋ Add %s" % (self._item_label_singular() or "item"))
            self.add_item_btn.setObjectName("addBtn")
            self.add_item_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.add_item_btn.clicked.connect(self._add_item_clicked)
            add_item_row.addWidget(self.add_item_btn)
            add_item_row.addStretch()
            self.scroll_layout.addLayout(add_item_row)

        self.scroll_layout.addStretch(1)

        scroll_area.setWidget(scroll_content)
        dialog_layout.addWidget(scroll_area, 1)

        # Actions
        actions = QHBoxLayout()
        actions.addStretch()

        cancel = QPushButton("Cancel")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.close)
        cancel.setFixedHeight(36)

        save = QPushButton("Save")
        save.setObjectName("saveBtn")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.clicked.connect(self._save_clicked)
        save.setFixedHeight(36)

        actions.addWidget(cancel)
        actions.addSpacing(8)
        actions.addWidget(save)
        dialog_layout.addLayout(actions)

        outer.addWidget(self.dialog)

        self.installEventFilter(self)

        # Build initial items from section_cfg
        self._load_initial_items()

        if not self.select_multiple:
            self._setup_exclusive_toggles()

    # ---------- UI building ----------

    def _build_section_visibility_block(self) -> QGroupBox:
        gb = QGroupBox("Section Visibility")
        gb.setStyleSheet("QGroupBox { font-weight: bold; }")
        lay = QVBoxLayout(gb)
        lay.setContentsMargins(80, 25, 80, 25)
        lay.setSpacing(10)

        row = QHBoxLayout()
        row.addWidget(QLabel("Include section in CV builder"))
        self.include_toggle = QToggle()
        included = self.section_cfg.get("enabled")
        self.include_toggle.setChecked(True if included is None else included)
        row.addWidget(self.include_toggle)
        row.addStretch()

        row.addWidget(QLabel("Preselect section in CV builder"))
        self.default_toggle = QToggle()
        preselected = self.section_cfg.get("preselected")
        self.default_toggle.setChecked(True if preselected is None else preselected)
        row.addWidget(self.default_toggle)
        lay.addLayout(row)

        gb_child = QGroupBox("Field Visibility")
        lay_child = QGridLayout(gb_child)

        self.field_toggles = {}
        field_visibility = self.section_cfg.get("field_visibility", {})
        current_row = 0
        current_col = 0
        for field in self.section_def.get("fields", []):
            field_label = QLabel(field["label"].title())
            field_toggle = QToggle()
            included = field_visibility.get(field["name"], True)
            field_toggle.setChecked(included)
            lay_child.addWidget(field_label, current_row, current_col, 1, 1, Qt.AlignmentFlag.AlignRight)
            lay_child.addWidget(field_toggle, current_row, current_col + 1, 1, 1, Qt.AlignmentFlag.AlignLeft)
            self.field_toggles[field["name"]] = field_toggle
            current_col += 2
            if current_col >= 6:
                current_row += 1
                current_col = 0
                
        if current_row == 0:
            while current_col <= 6:
                lay_child.addWidget(QWidget(), 0, current_col, 1, 1)
                current_col += 1
            
        lay.addWidget(gb_child)
        return gb

    def _item_label_singular(self) -> str:
        item_label = self.section_def.get("item_label") or {}
        return (item_label.get("singular") or "").strip()

    def _item_label_plural(self) -> str:
        item_label = self.section_def.get("item_label") or {}
        return (item_label.get("plural") or "").strip()

    def _fields_def(self) -> List[Dict[str, Any]]:
        fields = self.section_def.get("fields") or []
        return [f for f in fields if isinstance(f, dict) and f.get("name")]

    # ---------- Load initial data ----------

    def _load_initial_items(self) -> None:
        items = self.section_cfg.get("items")
        if not isinstance(items, list):
            items = []

        if not items:
            # ensure at least one item exists even if allow_multiple is false
            base_item = self._make_default_item_payload()
            items = [base_item]

        # If allow_multiple is false, keep only first
        if not self.allow_multiple and items:
            items = [items[0]]

        for payload in items:
            self._add_item_editor(payload)

    def _make_default_item_payload(self) -> Dict[str, Any]:
        """
        Returns an item payload shaped as:
          { field_name: "value" } OR
          { field_name: ["value", ... ] } for multiple fields.
        """
        out: Dict[str, Any] = {}
        for fdef in self._fields_def():
            fname = fdef["name"]
            is_multi = bool(fdef.get("allow_multiple", False))
            base = _field_default_value(fdef)

            if is_multi:
                out[fname] = [base]
            else:
                out[fname] = base
        return out

    # ---------- Item editors ----------

    def _add_item_clicked(self) -> None:
        payload = self._make_default_item_payload()
        self._add_item_editor(payload)

    def _add_item_editor(self, payload: Dict[str, Any]) -> None:
        editor = _ItemEditor(
            section_fields=self._fields_def(),
            payload=dict(payload or {}),
            palette=self.palette(),
            allow_multiple=self.allow_multiple,
            on_remove=lambda ed=None: self._remove_item_editor(editor),
        )
        self._item_widgets.append(editor)
        self.items_container.addWidget(editor)
        
        # Connect exclusive toggle behavior if needed
        if not self.select_multiple and self.allow_multiple and hasattr(editor, 'selected_toggle'):
            editor.selected_toggle.clicked.connect(
                lambda checked, current_editor=editor: self._handle_exclusive_toggle(current_editor, checked)
            )

        self._renumber_item_titles()

    def _remove_item_editor(self, editor: "_ItemEditor") -> None:
        if editor in self._item_widgets:
            self._item_widgets.remove(editor)
        editor.setParent(None)
        editor.deleteLater()
        self._renumber_item_titles()

    def _renumber_item_titles(self) -> None:
        label = self._item_label_singular() or "Item"
        for i, ed in enumerate(self._item_widgets, start=1):
            ed.set_title("%s %d" % (label, i))

    def _setup_exclusive_toggles(self) -> None:
        """Make toggles mutually exclusive when select_multiple is False."""
        if self.select_multiple or not self.allow_multiple:
            return
        
        for editor in self._item_widgets:
            if hasattr(editor, 'selected_toggle'):
                editor.selected_toggle.clicked.connect(
                    lambda checked, current_editor=editor: self._handle_exclusive_toggle(current_editor, checked)
                )

    def _handle_exclusive_toggle(self, clicked_editor: "_ItemEditor", checked: bool) -> None:
        """When one toggle is checked, uncheck all others."""
        if not checked or self.select_multiple:
            return
        
        for editor in self._item_widgets:
            if editor is not clicked_editor and hasattr(editor, 'selected_toggle'):
                editor.selected_toggle._user_checked = True
                editor.selected_toggle.setChecked(False)
                
    # ---------- Save / Close behaviour ----------

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
                self.close()  # close without saving
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def _save_clicked(self) -> None:
        if not self.section_name:
            QMessageBox.warning(self, "Missing section name", "This section has no 'name' in the YAML.")
            return

        # collect section payload
        section_payload: Dict[str, Any] = {
            "enabled": self.include_toggle.isChecked(),
            "preselected": self.default_toggle.isChecked(),
            "items": [ed.to_payload() for ed in self._item_widgets],
            "field_visibility": {name: t.isChecked() for name, t in self.field_toggles.items()},
        }

        # If allow_multiple is false, keep only one item
        if not self.allow_multiple and section_payload["items"]:
            section_payload["items"] = [section_payload["items"][0]]

        # write full config with only this section replaced
        full_cfg = load_full_config(self.config_path)
        full_cfg["cv_config"]["sections"][self.section_name] = section_payload
        save_full_config(self.config_path, full_cfg)

        if self.on_saved:
            self.on_saved(self.section_name, section_payload)

        self.close()
    
    def closeEvent(self, event):
        """Clean up when overlay is closed."""
        super().closeEvent(event)
        # Notify parent to clear reference
        parent = self.parentWidget()
        if parent and hasattr(parent, '_overlay') and parent._overlay is self:
            parent._overlay = None


class _ItemEditor(QFrame):
    def __init__(
        self,
        section_fields: List[Dict[str, Any]],
        payload: Dict[str, Any],
        palette: QPalette,
        allow_multiple: bool,
        on_remove: Callable[[], None],
        ):
        super().__init__()
        self.section_fields = section_fields
        self.payload = payload
        self.allow_multiple = allow_multiple
        self.on_remove = on_remove
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setObjectName("itemEditorFrame")
        self._field_editors: Dict[str, Union["_SingleFieldEditor", "_MultiFieldEditor"]] = {}
        
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        # GroupBox with title
        self.group_box = QGroupBox("Item")
        
        # Make title bold via stylesheet
        self.group_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        
        group_layout = QVBoxLayout(self.group_box)
        group_layout.setContentsMargins(80, 10, 80, 12)
        group_layout.setSpacing(12)
        
        
        # Remove button at the top right (if allowed)
        if allow_multiple:
            header = QHBoxLayout()
        header.addStretch()
        header.addStretch()

        if allow_multiple:
            header.addStretch()

        if allow_multiple:
            rm = QPushButton("Remove")
            rm.setCursor(Qt.CursorShape.PointingHandCursor)
            rm.clicked.connect(self.on_remove)
            rm.setFixedHeight(30)
            rm.setObjectName("editorRemoveBtn")
            self.selected_toggle = QToggle()
            included = self.payload.get("selected_default")
            self.selected_toggle.setChecked(False if included is None else included)
            header.addWidget(rm)
            header.addWidget(QLabel("Preselect in CV builder"))
            header.addWidget(self.selected_toggle)
            group_layout.addLayout(header)
        
        # Form fields
        form = QGridLayout()
        form.setHorizontalSpacing(100)
        form.setVerticalSpacing(4)
        
        current_row = 0
        current_col = 0
        for fdef in self.section_fields:
            fname = fdef["name"]
            flabel = fdef.get("label") or fname
            is_multi = bool(fdef.get("allow_multiple", False))
            show_name = bool(fdef.get("show_name", True))
            layout_width = str(fdef.get("layout_width", 'full'))
            initial = self.payload.get(fname)
            
            if is_multi:
                if not isinstance(initial, list):
                    initial = [initial]
                editor = _MultiFieldEditor(
                    palette=palette, 
                    fdef=fdef, 
                    initial_list=initial, 
                    show_name=show_name, 
                    flabel=flabel
                    )
            else:
                if initial is None:
                    initial = _field_default_value(fdef)
                editor = _SingleFieldEditor(fdef=fdef, initial_value=initial, show_name=show_name, flabel=flabel)
            self._field_editors[fname] = editor
            if layout_width == 'full' or is_multi:
                if current_col != 0:
                    current_row += 1
                    current_col = 0
                form.addWidget(editor, current_row, 0, 1, 2)
                current_row += 1
            elif layout_width == "half":
                form.addWidget(editor, current_row, current_col)
                current_col += 1
                if current_col >= 2:
                    current_row += 1
                    current_col = 0
        
        group_layout.addLayout(form)
        outer.addWidget(self.group_box)
        self.setStyleSheet("""
            QPushButton#editorRemoveBtn {
                background-color: rgba(220, 53, 69, 210);
                border: 1px solid rgba(220, 53, 69, 210);
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton#editorRemoveBtn:hover {
                background-color: rgba(220, 53, 69, 235);
            }
            """)

    def set_title(self, title: str) -> None:
        self.group_box.setTitle(title or "Item")

    def to_payload(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        out["selected_default"] = self.selected_toggle.isChecked()
        for fname, editor in self._field_editors.items():
            out[fname] = editor.to_payload()
        return out


class _SingleFieldEditor(QWidget):
    """
    Renders one field editor + 'Show field in CV Builder' checkbox.
    """

    def __init__(self, fdef: Dict[str, Any], initial_value: Any, show_name: bool, flabel: str):
        super().__init__()
        self.fdef = fdef

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.editor = _build_value_widget(fdef, initial_value)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        if show_name:
            label = QLabel(flabel)
            row.addWidget(label)

        row.addStretch()

        layout.addLayout(row)
        layout.addWidget(self.editor)

    def to_payload(self) -> Dict[str, Any]:
        return _read_value_widget(self.fdef, self.editor)



class _MultiFieldEditor(QWidget):
    """
    Renders a vertical list of value widgets. Each entry has:
      - value editor
      - 'Selected by Default' checkbox
      - optional remove button
    and an 'Add another' button at the end.
    """

    def __init__(
        self, 
        palette: QPalette,
        fdef: Dict[str, Any], 
        initial_list: List[Any], 
        show_name: bool, 
        flabel: str):
        super().__init__()
        self.fdef = fdef
        self.rows: List[Tuple[QWidget, Optional[QPushButton]]] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        self.rows_container = QVBoxLayout()
        self.rows_container.setContentsMargins(0, 0, 0, 0)
        self.rows_container.setSpacing(8)
        outer.addLayout(self.rows_container)

        for entry in (initial_list or []):
            if entry is None:
                entry = _field_default_value(fdef)
            self._add_row(value=entry, flabel=flabel, show_name=show_name)

        # ensure at least one
        if not self.rows:
            self._add_row(value=_field_default_value(fdef), flabel=flabel, show_name=show_name)

        add_row = QHBoxLayout()
        add_row.addStretch()
        add_btn = QPushButton("＋ Add another")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(lambda: self._add_row(value=_field_default_value(self.fdef), flabel=flabel))
        add_btn.setFixedHeight(30)
        add_btn.setObjectName("addFieldBtn")
        add_row.addWidget(add_btn)
        outer.addLayout(add_row)

        highlight = palette.color(QPalette.ColorRole.Highlight)

        self.setStyleSheet("""
            QPushButton#multifieldRemoveBtn {
                background-color: rgba(220, 53, 69, 210);
                border: 1px solid rgba(220, 53, 69, 210);
                color: white;
                border-radius: 6px;
                padding: 2px 10px;
                font-size: 12px;
                min-height: 18px;
                max-height: 18px;
            }
            QPushButton#multifieldRemoveBtn:hover {
                background-color: rgba(220, 53, 69, 235);
            }
            QPushButton#multifieldRemoveBtn:disabled {
                background-color: rgba(220, 53, 69, 80);
                border: 1px solid rgba(220, 53, 69, 80);
                color: rgba(255, 255, 255, 120);
            }
            QPushButton#addFieldBtn {
                background-color: %(hl)s;
                border: 1px solid %(hl)s;
                border-radius: 6px;
                padding: 2px 10px;
                font-size: 12px;
                min-height: 18px;
                max-height: 18px;
            }
            QPushButton#addFieldBtn:hover { background-color: %(hl2)s; }
            """
            % {
                "hl": highlight.name(),
                "hl2": highlight.darker(110).name(),
            })

    def _add_row(self, value: Any, flabel: str, show_name: bool) -> None:
        row_wrap = QWidget()
        row_l = QVBoxLayout(row_wrap)
        row_l.setContentsMargins(0, 0, 0, 0)
        row_l.setSpacing(6)

        controls = QHBoxLayout()

        if show_name:
            label = QLabel(flabel)
            controls.addWidget(label)
        controls.addStretch()

        remove_btn: Optional[QPushButton] = None
        if True:
            remove_btn = QPushButton("Remove")
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # remove_btn.setFixedHeight(28)
            remove_btn.setObjectName("multifieldRemoveBtn")
            controls.addWidget(remove_btn)

        row_l.addLayout(controls)

        editor = _build_value_widget(self.fdef, value)
        row_l.addWidget(editor)

        self.rows_container.addWidget(row_wrap)
        self.rows.append((editor, remove_btn))

        if remove_btn is not None:
            remove_btn.clicked.connect(lambda: self._remove_row(row_wrap))

        self._update_remove_enabled()

    def _remove_row(self, row_widget: QWidget) -> None:
        if len(self.rows) <= 1:
            return
        # find index
        idx = None
        for i, (ed, rb) in enumerate(self.rows):
            if row_widget is ed.parentWidget() or row_widget is rb.parentWidget() if rb else False:
                idx = i
                break
        # fallback: remove by widget match
        if idx is None:
            for i, (ed, rb) in enumerate(self.rows):
                if row_widget is ed.parentWidget():
                    idx = i
                    break

        # robust: remove by layout widget reference
        if idx is None:
            # remove last
            idx = len(self.rows) - 1

        # remove visual row
        row_widget.setParent(None)
        row_widget.deleteLater()

        # remove stored row (best-effort)
        if 0 <= idx < len(self.rows):
            self.rows.pop(idx)

        self._update_remove_enabled()

    def _update_remove_enabled(self) -> None:
        can_remove = len(self.rows) > 1
        for _, rb in self.rows:
            if rb is not None:
                rb.setEnabled(can_remove)

    def to_payload(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for editor, _ in self.rows:
            out.append(_read_value_widget(self.fdef, editor))
        return out


def _build_value_widget(fdef: Dict[str, Any], value: Any) -> QWidget:
    ftype = fdef.get("type")

    if ftype == "string":
        w = QLineEdit()
        w.setText("" if value is None else str(value))
        ph = (fdef.get("placeholder") or "").strip()
        if ph:
            w.setPlaceholderText(ph)
        return w

    if ftype == "multiline":
        w = QTextEdit()
        w.setPlainText("" if value is None else str(value))
        w.setFixedHeight(110)
        ph = (fdef.get("placeholder") or "").strip()
        if ph:
            w.setPlaceholderText(ph)
        return w

    if ftype == "enum":
        w = NoScrollComboBox()
        ADD_NEW = "Add new..."
        opts = fdef.get("options") or []
        if isinstance(opts, list):
            w.addItems([str(o) for o in opts])
        current = "" if value is None else str(value)
        idx = w.findText(current)
        w.setCurrentIndex(idx if idx >= 0 else 0)
        w.addItem(ADD_NEW)
        w.setEditable(False)

        def handle_activated(index):
            if w.itemText(index) != ADD_NEW:
                return

            w.setEditable(True)
            w.lineEdit().editingFinished.connect(finish_editing)
            w.clearEditText()
            w.lineEdit().setFocus()

        def finish_editing():
            text = w.currentText().strip()
            w.setEditable(False)
            added_idx = w.findText(text)
            if text and added_idx == -1:
                w.addItem(text)
            elif text:
                addnew_idx = w.findText(ADD_NEW)
                w.removeItem(addnew_idx)
                w.addItem(ADD_NEW)
            w.setCurrentText(text or w.itemText(0))

        w.activated.connect(handle_activated)

        return w

    if ftype == "year_month":
        # store as dict {"year": int, "month": int}
        y = None
        m = None
        if isinstance(value, dict):
            y = value.get("year")
            m = value.get("month")

        if not isinstance(y, int) or not isinstance(m, int):
            ty, tm = today_year_month()
            y, m = ty, tm

        wrap = QWidget()
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        year = NoScrollComboBox()
        # sensible range
        this_year = date.today().year
        years = list(range(this_year - 60, this_year + 6))
        year.addItems([str(v) for v in years])
        y_idx = year.findText(str(y))
        year.setCurrentIndex(y_idx if y_idx >= 0 else (year.count() - 1))
        year.setFixedWidth(70)

        month = NoScrollComboBox()
        month.addItems([str(v).zfill(2) for v in range(1, 13)])
        m_idx = month.findText(str(m).zfill(2))
        month.setCurrentIndex(m_idx if m_idx >= 0 else 0)
        month.setFixedWidth(70)

        wrap._year_combo = year  # type: ignore[attr-defined]
        wrap._month_combo = month  # type: ignore[attr-defined]

        lay.addWidget(year, 1)
        lay.addWidget(month, 1)
        lay.addStretch()
        return wrap

    if ftype == "number":
        w = QLineEdit()
        w.setValidator(QIntValidator())
        if value is None:
            value = 0
        try:
            w.setText(str(int(value)))
        except Exception:
            w.setText("0")
        return w

    if ftype == "object":
        gb = QGroupBox(fdef.get("label") or "Details")
        vlay = QVBoxLayout(gb)
        vlay.setContentsMargins(12, 10, 12, 12)
        vlay.setSpacing(10)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        fields = fdef.get("fields") or []
        if not isinstance(value, dict):
            value = _field_default_value(fdef)

        gb._sub_editors = {}  # type: ignore[attr-defined]

        for sub in fields:
            if not isinstance(sub, dict) or not sub.get("name"):
                continue
            sub_name = sub["name"]
            sub_label = sub.get("label") or sub_name
            sub_val = value.get(sub_name)
            editor = _build_value_widget(sub, sub_val)
            gb._sub_editors[sub_name] = (sub, editor)  # type: ignore[attr-defined]
            form.addRow(sub_label, editor)

        vlay.addLayout(form)
        return gb

    # fallback
    w = QLineEdit()
    w.setText("" if value is None else str(value))
    return w


def _read_value_widget(fdef: Dict[str, Any], widget: QWidget) -> Any:
    ftype = fdef.get("type")

    if ftype == "string":
        assert isinstance(widget, QLineEdit)
        return widget.text()

    if ftype == "multiline":
        assert isinstance(widget, QTextEdit)
        return widget.toPlainText()

    if ftype == "enum":
        assert isinstance(widget, NoScrollComboBox)
        return widget.currentText()

    if ftype == "year_month":
        year = widget._year_combo  # type: ignore[attr-defined]
        month = widget._month_combo  # type: ignore[attr-defined]
        try:
            y = int(year.currentText())
        except Exception:
            y = date.today().year
        try:
            m = int(month.currentText())
        except Exception:
            m = date.today().month
        return {"year": y, "month": m}

    if ftype == "number":
        assert isinstance(widget, QLineEdit)
        txt = (widget.text() or "").strip()
        if txt == "":
            return 0
        try:
            return int(txt)
        except Exception:
            return 0

    if ftype == "object":
        sub_map = widget._sub_editors  # type: ignore[attr-defined]
        out: Dict[str, Any] = {}
        for name, (sub_def, sub_w) in sub_map.items():
            out[name] = _read_value_widget(sub_def, sub_w)
        return out

    # fallback
    if isinstance(widget, QLineEdit):
        return widget.text()
    if isinstance(widget, QTextEdit):
        return widget.toPlainText()
    return None

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
        on_edit: Callable = None
    ) -> None:
        super().__init__(parent)

        self.section_def = section_def
        self.user_section = user_section or {}
        self.on_edit = on_edit

        self._init_ui()

    def _init_ui(self) -> None:
        # Main layout for this widget
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 10, 12, 10)
        root_layout.setSpacing(4)

        # Outer frame to give a card-like outline
        frame = QFrame(self)
        frame.setObjectName("sectionCardFrame")
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QFrame.Shadow.Raised)

        # Layout inside the frame
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(10, 8, 10, 8)
        frame_layout.setSpacing(4)

        # --- Derive data from defs + user profile ---
        section_type = self.section_def.get("name", "")
        default_title = self.section_def.get("default_title", section_type.title())

        title_override = self.user_section.get("title_override")
        title = title_override or default_title

        # Enabled / never_use flags
        status = self.user_section.get("enabled", True)

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
        if status:
            status_text = "Enabled"
        else:
            status_text = "Hidden"

        status_badge_color = STATUS_COLORS.get(status_text, "#6B7280")

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

        # --- Secondary row ---

        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)

        count_label = QLabel(count_text, frame)
        count_label.setObjectName("sectionCountLabel")

        meta_row.addWidget(count_label, stretch=0)

        self.edit_button = QPushButton(" Edit")
        self.edit_button.setIcon(EDIT_ICON)
        self.edit_button.setObjectName("sectionEditButton")
        self.edit_button.clicked.connect(self._handle_edit_clicked) 
        meta_row.addStretch()
        meta_row.addWidget(self.edit_button)

        frame_layout.addLayout(meta_row)

        root_layout.addWidget(frame)

        self.setStyleSheet(
            f"""
            QFrame#sectionCardFrame {{
                border: 1px solid #cccccc;
                border-radius: 6px;
            }}
            
            QLabel#sectionStatusLabel {{
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 11px;
                color: #ffffff;
                background-color: {status_badge_color};
            }}
            """
        )

    def _handle_edit_clicked(self):
        if callable(self.on_edit):
            # pass a job dict (same shape you already use elsewhere)
            self.on_edit(self.section_def, self.user_section)

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
        self._overlay = None

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

    def open_section_settings_overlay(self, section_def: dict, section_cfg_for_section: dict):
        if self._overlay is not None:
            self._overlay.deleteLater()
            self._overlay = None

        
        section_name = section_def.get("name")
        cv_cfg = load_cv_config(str(self.paths.get("config")))
        saved_section_cfg = cv_cfg.get("sections", {}).get(section_name, {})

        self._overlay = SectionSettingsOverlay(
            parent=self,
            palette=self.palette,
            section_def=section_def,
            section_cfg=saved_section_cfg,  # Use the actual saved config, not user_section
            config_path=str(self.paths.get("config")),
            on_saved=self._on_section_saved,  # Add callback to refresh UI
        )

        self._overlay.show()
        self._overlay.raise_()

    def _on_section_saved(self, section_name: str, payload: dict):
        """Callback when a section is saved - refresh the UI."""
        self._load_data_and_build_section_list()

    # ----------------------
    # Data loading
    # ----------------------

    def _load_data_and_build_section_list(self) -> None:
        self.section_defs = self._load_section_names_from_yaml()
        self.user_profile = load_cv_config(self.paths.get("config"))["sections"]

        # Clear previous cards if any
        while self.section_list_layout.count():
            item = self.section_list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        for section_def in self.section_defs:
            section_name = section_def.get("name")
            user_section = self.user_profile.get(section_name)

            card = SectionCard(section_def, user_section, parent=self.section_list_container, on_edit=self.open_section_settings_overlay)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            self.section_list_layout.addWidget(card)

        self.section_list_layout.addStretch(1)

    @staticmethod
    def _load_section_names_from_yaml() -> list[dict]:
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

    def resizeEvent(self, event):
        """Handle window resize - update overlay if it's open."""
        super().resizeEvent(event)
        
        # Update overlay geometry when window is resized
        if self._overlay is not None and self._overlay.isVisible():
            self._overlay.setGeometry(self.rect())
