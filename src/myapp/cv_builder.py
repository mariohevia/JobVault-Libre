from pathlib import Path
from typing import Any, Callable
from functools import partial

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
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
    QScrollArea,
    QSizePolicy,
    QGroupBox,
    QMessageBox,
    )

from PyQt6.QtGui import QIcon, QPalette, QFont, QShowEvent
from PyQt6.QtCore import (
    Qt, 
    pyqtSignal, 
    QDate, 
    QStringListModel, 
    QEvent,
    QObject,
    )

from myapp.database import JobDatabase
from myapp.utils import (
    field_default_value,
    load_section_names_from_yaml,
    load_cv_config,
    load_full_config,
    save_full_config,
    )
from myapp.widgets import NoScrollDateEdit, NoScrollComboBox
from myapp.cv_config import (
    _build_value_widget,
    _read_value_widget,
    _ItemEditor,
    )
from myapp.icons import (
    SearchIcon,
    FilterIcon,
    CloseIcon,
    )
from myapp.constants import (
    STATUS_OPTIONS,
    JOB_TYPE_OPTIONS,
    WORK_ARRANGEMENT_OPTIONS,
    )

class BaseOverlay(QWidget):
    """
    Base class for full-parent overlays with a centred dialog panel.
    
    Closing behaviour (X button, Escape key, click-outside) is handled here
    and works identically for every subclass.
    """

    def __init__(self, parent: QWidget, title: str) -> None:
        super().__init__(parent)
        self._title_text = title
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setObjectName("overlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.installEventFilter(self)

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the fixed outer structure: backdrop -> dialog -> sections."""
        # ── Outer frame and layouts ──────────────────────────────────────────
        self.dialog = QFrame(self)
        self.dialog.setObjectName("dialogFrame")
        self.dialog.setMinimumSize(200, 200)
        self.dialog.setMaximumWidth(600)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(60, 40, 60, 80)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        root_layout.addWidget(self.dialog)

        dialog_layout = QVBoxLayout(self.dialog)
        dialog_layout.setContentsMargins(24, 20, 24, 24)
        dialog_layout.setSpacing(16)

        # ── Title row (NOT scrollable) ───────────────────────────────────────
        title_row = QHBoxLayout()

        title_label = QLabel(self._title_text)
        title_label.setObjectName("dialogTitle")
        title_label.setStyleSheet("font-weight: 600; font-size: 18px;")

        close_btn = QPushButton("")
        close_btn.setIcon(CloseIcon())
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(32, 32)

        title_row.addWidget(title_label)
        title_row.addStretch()
        title_row.addWidget(close_btn)

        dialog_layout.addLayout(title_row)

        # ── Form ─────────────────────────────────────────────────────────────
        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(10)

        self._build_form(form_layout)
        dialog_layout.addLayout(form_layout)

        # ── Action buttons (NOT scrollable) ──────────────────────────────────
        actions = QHBoxLayout()
        actions.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.close)
        cancel_btn.setFixedHeight(36)

        save_current_btn = QPushButton("Save for this CV")
        save_current_btn.setObjectName("saveCurrentBtn")
        save_current_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_current_btn.clicked.connect(
            partial(self._persist, all_cvs = False)
            )
        save_current_btn.setFixedHeight(36)

        save_all_btn = QPushButton("Save for all CVs")
        save_all_btn.setObjectName("saveAllBtn")
        save_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_all_btn.clicked.connect(
            partial(self._persist, all_cvs = True)
            )
        save_all_btn.setFixedHeight(36)

        actions.addWidget(cancel_btn)
        actions.addSpacing(8)
        actions.addWidget(save_current_btn)
        actions.addSpacing(8)
        actions.addWidget(save_all_btn)

        dialog_layout.addLayout(actions)

    def _persist(self, all_cvs: bool) -> None:
        """
        Persist the data into the current cv or the cv configuration.
        Subclasses must override this.
        """
        #TODO: Ensure that this cannot be done the same for all overlays.
        raise NotImplementedError

    def _build_form(self, scroll_layout: QVBoxLayout) -> None:
        """
        Populate the scrollable area.  Called once during `__init__`.
        Subclasses must override this.
        """
        raise NotImplementedError

    def _fit_to_parent(self) -> None:
        """Resize overlay to match parent widget."""
        p = self.parentWidget()
        if p is not None:
            self.setGeometry(p.rect())

    def showEvent(self, event: QShowEvent) -> None:
        """Resize overlay to match parent widget when showed."""
        super().showEvent(event)
        self._fit_to_parent()
        self._on_show()

    def resizeEvent(self, event: QShowEvent) -> None:
        """Handle window resize to keep overlay covering parent."""
        super().resizeEvent(event)
        self._fit_to_parent()

    def _on_show(self) -> None:
        """
        Called at the end of `showEvent`.  Override to, e.g., set
        initial focus on a form field.
        """
        return

    def eventFilter(self, obj: QObject, event: QShowEvent) -> bool:
        """Close overlay when clicking outside the dialog panel."""
        if obj is self and event.type() == QEvent.Type.MouseButtonPress:
            if not self.dialog.geometry().contains(event.position().toPoint()):
                self.close()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QShowEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class _FieldEditOverlay(BaseOverlay):
    """
    Edit a single field (identified by fdef) for a specific item_index.
    For allow_multiple fields this edits one *entry* inside the list,
    identified by entry_index.
    """

    def __init__(
        self,
        parent: QWidget,
        section_def: dict[str, Any],
        section_cfg: dict[str, Any],
        item_index: int,
        field_name: str,
        config_path: str,
        entry_index: int | None = None,
        on_saved: Callable[[str, Any, bool], None] | None = None,
        ):

        section_def = dict(section_def)
        self.section_cfg = dict(section_cfg)
        self.item_index = item_index
        self.field_name = field_name
        self.entry_index = entry_index
        self.config_path = config_path
        self.on_saved = on_saved
        self.section_name = section_def["name"].strip()

        self.fdef = next(
            (f for f in (section_def["fields"])
            if f["name"] == field_name)
            )
        flabel = self.fdef.get("label") or field_name
        super().__init__(parent, f"Edit {flabel}")

    def _build_form(self, scroll_layout: QVBoxLayout) -> None:
        items = self.section_cfg.get("items") or []
        item_payload = dict(items[self.item_index]) if 0 <= self.item_index < len(items) else {}
        raw = item_payload.get(self.field_name)

        if self.entry_index is not None:
            # Editing one entry inside an allow_multiple list
            entries = raw if isinstance(raw, list) else []
            current_value = entries[self.entry_index] if 0 <= self.entry_index < len(entries) else field_default_value(self.fdef)
        else:
            current_value = raw if raw is not None else field_default_value(self.fdef)

        # The single value editor widget
        self._editor = _build_value_widget(self.fdef, current_value)
        scroll_layout.addWidget(self._editor)

    def _persist(self, all_cvs: bool) -> None:
        if not self.section_name:
            QMessageBox.warning(self, "Error", "Section has no name.")
            return

        new_value = _read_value_widget(self.fdef, self._editor)

        full_cfg = load_full_config(self.config_path)
        cv_config = full_cfg.get("cv_config", {})
        sections = cv_config.get("sections", {})

        def _patch_section(sec: dict) -> dict:
            sec = dict(sec)
            items = list(sec.get("items") or [])
            while len(items) <= self.item_index:
                items.append({})
            item = dict(items[self.item_index])

            if self.entry_index is not None:
                # Patch one entry inside the list
                entries = list(item.get(self.field_name) or [])
                while len(entries) <= self.entry_index:
                    entries.append(field_default_value(self.fdef))
                entries[self.entry_index] = new_value
                item[self.field_name] = entries
            else:
                item[self.field_name] = new_value

            items[self.item_index] = item
            sec["items"] = items
            return sec

        if all_cvs:
            for key in list(sections.keys()):
                if key == self.section_name:
                    sections[key] = _patch_section(sections[key])
        else:
            sections[self.section_name] = _patch_section(
                sections.get(self.section_name, {})
            )

        cv_config["sections"] = sections
        full_cfg["cv_config"] = cv_config
        save_full_config(self.config_path, full_cfg)

        if self.on_saved:
            self.on_saved(self.section_name, new_value, all_cvs)

        self.close()

    def closeEvent(self, event):
        super().closeEvent(event)
        p = self.parentWidget()
        if p and hasattr(p, "_field_overlay") and p._field_overlay is self:
            p._field_overlay = None


# ---------------------------------------------------------------------------
# _AddEntryOverlay  — append one entry to an allow_multiple field
# ---------------------------------------------------------------------------

class _AddEntryOverlay(BaseOverlay):
    """
    Adds a single new entry to an allow_multiple field inside an existing item.
    """

    def __init__(
        self,
        parent: QWidget,
        section_def: dict[str, Any],
        section_cfg: dict[str, Any],
        item_index: int,
        field_name: str,
        config_path: str,
        on_saved: Callable[[str, Any, bool], None] | None = None,
        ):
        self.section_def  = dict(section_def or {})
        self.section_cfg  = dict(section_cfg or {})
        self.item_index   = item_index
        self.field_name   = field_name
        self.config_path  = config_path
        self.on_saved     = on_saved
        self.section_name = (self.section_def.get("name") or "").strip()

        self.fdef = next(
            (f for f in (section_def.get("fields") or [])
             if isinstance(f, dict) and f.get("name") == field_name),
            {}
        )
        flabel = self.fdef.get("label") or field_name
        super().__init__(parent, f"Add {flabel}")

    def _build_form(self, scroll_layout: QVBoxLayout) -> None:
        self._editor = _build_value_widget(self.fdef, field_default_value(self.fdef))
        scroll_layout.addWidget(self._editor)

    def _persist(self, all_cvs: bool) -> None:
        if not self.section_name:
            QMessageBox.warning(self, "Error", "Section has no name.")
            return

        new_value = _read_value_widget(self.fdef, self._editor)

        full_cfg  = load_full_config(self.config_path)
        cv_config = full_cfg.get("cv_config", {})
        sections  = cv_config.get("sections", {})

        def _patch_section(sec: dict) -> dict:
            sec   = dict(sec)
            items = list(sec.get("items") or [])
            while len(items) <= self.item_index:
                items.append({})
            item    = dict(items[self.item_index])
            entries = list(item.get(self.field_name) or [])
            entries.append(new_value)
            item[self.field_name] = entries
            items[self.item_index] = item
            sec["items"] = items
            return sec

        if all_cvs:
            for key in list(sections.keys()):
                if key == self.section_name:
                    sections[key] = _patch_section(sections[key])
        else:
            sections[self.section_name] = _patch_section(
                sections.get(self.section_name, {})
            )

        cv_config["sections"] = sections
        full_cfg["cv_config"] = cv_config
        save_full_config(self.config_path, full_cfg)

        if self.on_saved:
            self.on_saved(self.section_name, new_value, all_cvs)

        self.close()

    def closeEvent(self, event):
        super().closeEvent(event)
        p = self.parentWidget()
        if p and hasattr(p, "_add_entry_overlay") and p._add_entry_overlay is self:
            p._add_entry_overlay = None


# ---------------------------------------------------------------------------
# _AddItemOverlay  — add a brand-new item (all fields at once)
# ---------------------------------------------------------------------------

class _AddItemOverlay(BaseOverlay):
    """Adds a complete new item to the section."""

    def __init__(
        self,
        parent: QWidget,
        section_def: dict[str, Any],
        section_cfg: dict[str, Any],
        config_path: str,
        on_saved: Callable[[str, dict[str, Any], bool], None] | None = None,
    ):
        self.section_def  = dict(section_def or {})
        self.section_cfg  = dict(section_cfg or {})
        self.config_path  = config_path
        self.on_saved     = on_saved
        self.section_name = (self.section_def.get("name") or "").strip()
        self.allow_multiple = bool(self.section_def.get("allow_multiple", False))

        singular = (self.section_def.get("item_label") or {}).get("singular") or "Item"
        super().__init__(parent, f"Add {singular}")

    def _build_form(self, scroll_layout: QVBoxLayout) -> None:
        self._item_editor = _ItemEditor(
            section_fields=self._fields_def(),
            payload=self._make_default_item_payload(),
            allow_multiple=self.allow_multiple,
            on_remove=lambda: None,
        )
        scroll_layout.addWidget(self._item_editor)

    def _fields_def(self) -> list[dict[str, Any]]:
        fields = self.section_def.get("fields") or []
        return [f for f in fields if isinstance(f, dict) and f.get("name")]

    def _make_default_item_payload(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for fdef in self._fields_def():
            fname    = fdef["name"]
            is_multi = bool(fdef.get("allow_multiple", False))
            base     = field_default_value(fdef)
            out[fname] = [base] if is_multi else base
        return out

    def _persist(self, all_cvs: bool) -> None:
        if not self.section_name:
            QMessageBox.warning(self, "Error", "Section has no name.")
            return

        new_item  = self._item_editor.to_payload()
        full_cfg  = load_full_config(self.config_path)
        cv_config = full_cfg.get("cv_config", {})
        sections  = cv_config.get("sections", {})

        def _patch(sec: dict) -> dict:
            sec   = dict(sec)
            items = list(sec.get("items") or [])
            items.append(new_item)
            sec["items"] = items
            return sec

        if all_cvs:
            for key in list(sections.keys()):
                if key == self.section_name:
                    sections[key] = _patch(sections[key])
        else:
            sections[self.section_name] = _patch(sections.get(self.section_name, {}))

        cv_config["sections"] = sections
        full_cfg["cv_config"] = cv_config
        save_full_config(self.config_path, full_cfg)

        if self.on_saved:
            self.on_saved(self.section_name, new_item, all_cvs)

        self.close()

    def closeEvent(self, event):
        super().closeEvent(event)
        p = self.parentWidget()
        if p and hasattr(p, "_add_overlay") and p._add_overlay is self:
            p._add_overlay = None


# ---------------------------------------------------------------------------
# Read-only value renderer
# ---------------------------------------------------------------------------

def _render_value_readonly(fdef: dict[str, Any], value: Any) -> QWidget:
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
        gb   = QGroupBox(fdef.get("label") or "Details")
        gb.setObjectName("readonlyObjectGroup")
        vlay = QVBoxLayout(gb)
        vlay.setContentsMargins(12, 10, 12, 10)
        vlay.setSpacing(6)
        fields   = fdef.get("fields") or []
        val_dict = value if isinstance(value, dict) else {}
        for sub in fields:
            if not isinstance(sub, dict) or not sub.get("name"):
                continue
            sub_name  = sub["name"]
            sub_label = sub.get("label") or sub_name
            sub_val   = val_dict.get(sub_name)
            row = QHBoxLayout()
            row.addWidget(QLabel(f"<b>{sub_label}:</b>"))
            row.addWidget(_render_value_readonly(sub, sub_val))
            row.addStretch()
            vlay.addLayout(row)
        return gb

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


# ---------------------------------------------------------------------------
# _ReadonlyItemView  — shows one item, field by field, each with its own ✎ btn
# ---------------------------------------------------------------------------

class _ReadonlyItemView(QFrame):
    """
    Displays one item's fields in read-only form.

    Each *scalar* field has a small ✎ button to its right that opens
    _FieldEditOverlay for that field only.

    Each *allow_multiple* field shows its entries as a list, each entry
    with its own ✎ button, plus a ＋ button at the bottom of the list.
    """

    def __init__(
        self,
        section_fields: list[dict[str, Any]],
        payload: dict[str, Any],
        title: str,
        item_index: int,
        allow_multiple: bool,          # whether the *section* allows multiple items
        on_edit_field: Callable[[str, int | None], None],   # (field_name, entry_index|None)
        on_add_entry: Callable[[str], None],
    ):
        super().__init__()
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setObjectName("readonlyItemFrame")

        highlight  = self.palette().color(QPalette.ColorRole.Highlight)
        border_col = self.palette().color(QPalette.ColorRole.Window).lighter(140)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.group_box = QGroupBox(title)
        self.group_box.setStyleSheet("QGroupBox { font-weight: bold; }")
        gb_layout = QVBoxLayout(self.group_box)
        gb_layout.setContentsMargins(16, 12, 16, 14)
        gb_layout.setSpacing(10)

        # Preselected badge (only meaningful when section allow_multiple=True)
        if allow_multiple:
            hdr = QHBoxLayout()
            hdr.addStretch()
            selected = payload.get("selected_default", False)
            badge_text = "Preselected" if selected else "Not preselected"
            badge_color = "#10B981" if selected else "#777777"
            badge = QLabel(badge_text)
            badge.setStyleSheet(
                f"border-radius: 10px; padding: 2px 8px; font-size: 11px;"
                f" color: #ffffff; background-color: {badge_color};"
            )
            hdr.addWidget(badge)
            gb_layout.addLayout(hdr)

        # ── Field rows ──────────────────────────────────────────────────────
        # Single QGridLayout for all fields, mirroring _ItemEditor exactly:
        # is_multi and layout_width='full' span both columns; 'half' shares a row.
        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        current_row = 0
        current_col = 0

        for fdef in section_fields:
            fname = fdef["name"]
            flabel = fdef.get("label") or fname
            is_multi = bool(fdef.get("allow_multiple", False))
            layout_width = str(fdef.get("layout_width", "full"))
            raw_value = payload.get(fname)

            if is_multi:
                # ── allow_multiple field: list of entries ──────────────────
                field_block = QWidget()
                block_lay   = QVBoxLayout(field_block)
                block_lay.setContentsMargins(0, 0, 0, 0)
                block_lay.setSpacing(4)

                # Label + ＋ add button on the same row
                lbl_row = QHBoxLayout()
                lbl_row.addWidget(QLabel(f"<b>{flabel}</b>"))
                lbl_row.addStretch()
                add_entry_btn = QPushButton("＋ Add")
                add_entry_btn.setObjectName("addEntryBtn")
                add_entry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                add_entry_btn.setFixedHeight(22)
                add_entry_btn.clicked.connect(
                    lambda _checked, fn=fname: on_add_entry(fn)
                )
                lbl_row.addWidget(add_entry_btn)
                block_lay.addLayout(lbl_row)

                entries = raw_value if isinstance(raw_value, list) else (
                    [raw_value] if raw_value is not None else []
                )
                for ei, entry in enumerate(entries):
                    entry_row = QHBoxLayout()
                    entry_row.setContentsMargins(8, 0, 0, 0)
                    edit_btn  = QPushButton("✎")
                    edit_btn.setObjectName("fieldEditBtn")
                    edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    edit_btn.setFixedSize(24, 24)
                    edit_btn.setToolTip(f"Edit this {flabel} entry")
                    edit_btn.clicked.connect(
                        lambda _checked, fn=fname, idx=ei: on_edit_field(fn, idx)
                    )
                    entry_row.addWidget(edit_btn)
                    val_lbl = _render_value_readonly(fdef, entry)
                    entry_row.addWidget(val_lbl, stretch=1)
                    block_lay.addLayout(entry_row)

                if not entries:
                    empty_lbl = QLabel("—")
                    empty_lbl.setContentsMargins(8, 0, 0, 0)
                    block_lay.addWidget(empty_lbl)

                widget = field_block

            else:
                # ── scalar field: ✎ on the left, then label + value ────────
                cell = QWidget()
                cell_lay = QVBoxLayout(cell)
                cell_lay.setContentsMargins(0, 0, 0, 0)
                cell_lay.setSpacing(6)
                cell_lay.addWidget(QLabel(f"<b>{flabel}</b>"))

                edit_val = QWidget()
                edit_val_lay = QHBoxLayout(edit_val)

                edit_btn = QPushButton("✎")
                edit_btn.setObjectName("fieldEditBtn")
                edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                edit_btn.setFixedSize(24, 24)
                edit_btn.setToolTip(f"Edit {flabel}")
                edit_btn.clicked.connect(
                    lambda _checked, fn=fname: on_edit_field(fn, None)
                )
                edit_val_lay.addWidget(edit_btn, alignment=Qt.AlignmentFlag.AlignTop)

                edit_val_lay.setContentsMargins(0, 0, 0, 0)
                edit_val_lay.setSpacing(2)
                edit_val_lay.addWidget(_render_value_readonly(fdef, raw_value))
                cell_lay.addWidget(edit_val, stretch=1)

                widget = cell

            if layout_width == "full" or is_multi:
                if current_col != 0:
                    current_row += 1
                    current_col = 0
                form.addWidget(widget, current_row, 0, 1, 2)
                current_row += 1
            else:  # 'half'
                form.addWidget(widget, current_row, current_col)
                current_col += 1
                if current_col >= 2:
                    current_row += 1
                    current_col = 0

        gb_layout.addLayout(form)

        outer.addWidget(self.group_box)

        self.setStyleSheet(f"""
            QPushButton#fieldEditBtn {{
                border: 1px solid {border_col.name()};
                border-radius: 4px;
                font-size: 13px;
                padding: 0px;
            }}
            QPushButton#fieldEditBtn:hover {{
                background-color: {highlight.name()};
                color: white;
            }}
            QPushButton#addEntryBtn {{
                background-color: {highlight.name()};
                border: 1px solid {highlight.name()};
                border-radius: 4px;
                padding: 0px 6px;
                font-size: 11px;
                color: white;
            }}
            QPushButton#addEntryBtn:hover {{
                background-color: {highlight.darker(110).name()};
            }}
        """)

    def set_title(self, title: str) -> None:
        self.group_box.setTitle(title or "Item")


# ---------------------------------------------------------------------------
# SectionSelectionPage
# ---------------------------------------------------------------------------

class SectionSelectionPage(QWidget):
    """
    Read-only display page for a single section's saved data.

    • Each field has a ✎ button that opens a single-field edit overlay.
    • allow_multiple fields also show a + Add button per field.
    • A footer "+ Add <item>" button (only when section allow_multiple=True)
      opens the full new-item overlay (_AddItemOverlay).
    """

    def __init__(
        self,
        section_def: dict[str, Any],
        config_path: str,
        parent: QWidget | None = None,
        on_item_saved: Callable[[str, dict[str, Any], bool], None] | None = None,
    ):
        super().__init__(parent)

        self.palette_ref = self.palette()
        self.cv_container = parent
        if not isinstance(section_def, dict):
            raise TypeError(
                f"SectionSelectionPage: section_def must be a dict, got "
                f"{type(section_def).__name__!r}: {section_def!r}."
            )
        self.section_def = dict(section_def)
        self.config_path = config_path
        self.on_item_saved = on_item_saved

        self.section_name = (self.section_def.get("name") or "").strip()
        self.allow_multiple = bool(self.section_def.get("allow_multiple", False))

        self._field_overlay: _FieldEditOverlay | None = None
        self._add_entry_overlay: _AddEntryOverlay | None  = None
        self._add_overlay: _AddItemOverlay | None   = None

        self._init_ui()
        self._load_and_render()

    # ------------------------------------------------------------------
    # UI skeleton
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

        # Header row
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        self._title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self._title_label.setFont(title_font)
        header_row.addWidget(self._title_label, stretch=1)

        self.main_layout.addLayout(header_row)

        # Description
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
        self._items_layout   = QVBoxLayout(self._scroll_content)
        self._items_layout.setContentsMargins(0, 0, 8, 0)
        self._items_layout.setSpacing(12)
        self._items_layout.addStretch(1)

        scroll_area.setWidget(self._scroll_content)
        self.main_layout.addWidget(scroll_area, stretch=1)

        # Footer: Add item (only for section allow_multiple)
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

        self.setStyleSheet(f"""
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
            QLabel#readonlyValue {{ padding: 2px 0px; }}
            QLabel#sectionDescLabel {{ color: gray; font-size: 11px; }}
            QScrollArea#itemsScrollArea {{ border: none; background: transparent; }}
        """)

    # ------------------------------------------------------------------
    # Data loading & rendering
    # ------------------------------------------------------------------

    def _load_section_cfg(self) -> dict[str, Any]:
        cv_cfg = self.cv_container.get_current_cv()
        return cv_cfg.get("sections").get(self.section_name)

    def _load_and_render(self) -> None:
        self._render(self._load_section_cfg())

    def _render(self, section_cfg: dict[str, Any]) -> None:
        # Header
        default_title = self.section_def.get("default_title") or self.section_name.title()
        title = section_cfg.get("title_override") or default_title
        self._title_label.setText(title)

        desc = (self.section_def.get("description") or "").strip()
        self._desc_label.setText(desc)
        self._desc_label.setVisible(bool(desc))

        singular = (self.section_def.get("item_label") or {}).get("singular") or "Item"
        self._add_btn.setText(f"＋ Add {singular}")
        self._add_btn.setVisible(self.allow_multiple)

        # Clear existing item views (keep trailing stretch)
        while self._items_layout.count() > 1:
            item = self._items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Rebuild
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
            item_title = f"{singular} {idx + 1}" if len(items) > 1 else singular

            view = _ReadonlyItemView(
                section_fields=fields_def,
                payload=payload,
                title=item_title,
                item_index=idx,
                allow_multiple=self.allow_multiple,
                on_edit_field=lambda fn, ei, i=idx: self._open_field_overlay(i, fn, ei),
                on_add_entry=lambda fn, i=idx: self._open_add_entry_overlay(i, fn),
                )
            view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self._items_layout.insertWidget(self._items_layout.count() - 1, view)

    # ------------------------------------------------------------------
    # Overlay launchers
    # ------------------------------------------------------------------

    def _open_field_overlay(self, item_index: int, field_name: str, entry_index: int | None) -> None:
        if self._field_overlay is not None:
            self._field_overlay.deleteLater()
            self._field_overlay = None

        self._field_overlay = _FieldEditOverlay(
            parent=self,
            section_def=self.section_def,
            section_cfg=self._load_section_cfg(),
            item_index=item_index,
            field_name=field_name,
            config_path=self.config_path,
            entry_index=entry_index,
            on_saved=self._on_saved,
        )
        self._field_overlay.show()
        self._field_overlay.raise_()

    def _open_add_entry_overlay(self, item_index: int, field_name: str) -> None:
        if self._add_entry_overlay is not None:
            self._add_entry_overlay.deleteLater()
            self._add_entry_overlay = None

        self._add_entry_overlay = _AddEntryOverlay(
            parent=self,
            section_def=self.section_def,
            section_cfg=self._load_section_cfg(),
            item_index=item_index,
            field_name=field_name,
            config_path=self.config_path,
            on_saved=self._on_saved,
        )
        self._add_entry_overlay.show()
        self._add_entry_overlay.raise_()

    def _open_add_overlay(self) -> None:
        if self._add_overlay is not None:
            self._add_overlay.deleteLater()
            self._add_overlay = None

        self._add_overlay = _AddItemOverlay(
            parent=self,
            section_def=self.section_def,
            section_cfg=self._load_section_cfg(),
            config_path=self.config_path,
            on_saved=self._on_saved,
        )
        self._add_overlay.show()
        self._add_overlay.raise_()

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_saved(self, section_name: str, value: Any, all_cvs: bool) -> None:
        self._load_and_render()
        if self.on_item_saved:
            self.on_item_saved(section_name, value, all_cvs)

    def _on_settings_saved(self, section_name: str, section_payload: dict[str, Any]) -> None:
        self._load_and_render()

    # ------------------------------------------------------------------
    # Resize: keep overlays in sync
    # ------------------------------------------------------------------

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for overlay in (
            self._field_overlay,
            self._add_entry_overlay,
            self._add_overlay,
        ):
            if overlay is not None and overlay.isVisible():
                overlay.setGeometry(self.rect())

    def showEvent(self, event):
        super().showEvent(event)
        self._load_and_render()


# ---------------------------------------------------------------------------
# Everything below is unchanged from the original file
# ---------------------------------------------------------------------------

class CVListPage(QWidget):

    create_cv_clicked = pyqtSignal()

    def __init__(
        self,
        db: "JobDatabase",
        paths: dict[str, Path],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.db = db
        self.paths = paths
        self._build_ui()
        self._load_data()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        top_bar = QHBoxLayout()
        title_label = QLabel("Curriculum Vitae")
        title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        add_button = QPushButton("Create new CV")
        add_button.setFixedHeight(32)
        add_button.clicked.connect(self._on_create_cv)
        top_bar.addWidget(title_label)
        top_bar.addStretch()
        top_bar.addWidget(add_button)
        main_layout.addLayout(top_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Title", "Created", "Updated", "Newest Version ID", "Group ID", "Actions",
        ])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        main_layout.addWidget(self.table)

    def _load_data(self) -> None:
        groups = self.db.get_all_cv_groups()
        self.table.setRowCount(len(groups))
        for row, (group_id, title, created_at, updated_at, newest_version_id) in enumerate(groups):
            self.table.setItem(row, 0, QTableWidgetItem(title))
            self.table.setItem(row, 1, QTableWidgetItem(created_at))
            self.table.setItem(row, 2, QTableWidgetItem(updated_at))
            self.table.setItem(row, 3, QTableWidgetItem(str(newest_version_id) if newest_version_id else ""))
            self.table.setItem(row, 4, QTableWidgetItem(str(group_id)))
            self.table.setCellWidget(row, 5, self._create_actions_cell())

    def _on_create_cv(self) -> None:
        self.create_cv_clicked.emit()

    def _create_actions_cell(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for icon_name, tip in [
            ("document-open", "View CV"),
            ("document-edit", "Edit CV"),
            ("edit-delete", "Delete CV"),
        ]:
            btn = QToolButton()
            btn.setIcon(QIcon.fromTheme(icon_name))
            btn.setToolTip(tip)
            layout.addWidget(btn)
        return container

    def _set_column_widths(self) -> None:
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        self.table.resizeColumnsToContents()
        total_width    = self.table.width()
        current_widths = [self.table.columnWidth(i) for i in range(self.table.columnCount())]
        current_total  = sum(current_widths)
        extra_space    = total_width - current_total
        for i in range(self.table.columnCount()):
            proportion = current_widths[i] / current_total
            self.table.setColumnWidth(i, int(current_widths[i] + proportion * extra_space))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._set_column_widths()


class CVTopNavigator(QWidget):
    section_selected = pyqtSignal(str)
    back_clicked = pyqtSignal()

    def __init__(self, section_defs: list, parent: QWidget | None = None):
        super().__init__(parent)
        self.section_defs = section_defs
        self.current_section = None
        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(8)

        top_row = QHBoxLayout()
        back_btn = QPushButton("Cancel")
        back_btn.clicked.connect(self.back_clicked.emit)
        back_btn.setFixedHeight(32)
        back_btn.setFixedWidth(80)
        title_label = QLabel("CV title:")
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

        nav_row = QHBoxLayout()
        nav_row.setSpacing(0)
        self.nav_buttons = {}

        self._create_nav_button("target_application", "Target Application", nav_row)
        for section_def in self.section_defs:
            section_name  = section_def.get("name")
            section_label = section_def.get("default_title", section_name)
            self._create_nav_button(section_name, section_label, nav_row)
        self._create_nav_button("reorder_sections", "Reorder", nav_row)
        self._create_nav_button("preview", "Preview", nav_row)
        main_layout.addLayout(nav_row)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(divider)

    def _create_nav_button(self, section_name: str, label: str, nav_row: QHBoxLayout) -> QPushButton:
        btn = QPushButton(label)
        btn.setFixedHeight(28)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self._on_nav_clicked(section_name))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid palette(mid);
                border-bottom: none;
                padding: 6px 12px;
                font-size: 13px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }
            QPushButton:hover {
                background-color: palette(alternate-base);
                border: 2px solid palette(mid);
                border-bottom: none;
            }
            QPushButton:checked {
                background-color: palette(highlight);
                color: palette(highlighted-text); font-weight: 600;
            }
        """)
        self.nav_buttons[section_name] = btn
        nav_row.addWidget(btn)
        return btn

    def _on_nav_clicked(self, section_name: str) -> None:
        self.set_active_section(section_name)
        self.section_selected.emit(section_name)

    def set_active_section(self, section_name: str) -> None:
        self.current_section = section_name
        for name, btn in self.nav_buttons.items():
            btn.setChecked(name == section_name)


class SectionPlaceholderPage(QWidget):
    """Placeholder page for each CV section"""

    def __init__(self, section_name: str, section_label: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.section_name  = section_name
        self.section_label = section_label
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        title = QLabel(self.section_label)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(title)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(divider)

        placeholder = QLabel(
            f"This is a placeholder for the '{self.section_label}' section.\n\n"
            f"Content will be implemented later."
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: palette(mid); font-size: 14px; padding: 40px;")
        layout.addWidget(placeholder, stretch=1)


class TargetApplicationPage(QWidget):
    """Page to select the targeted job application for the CV"""

    ROWS_COMPLETER = 2
    TABLE_HEADERS  = ["Date applied", "Position", "Company", "Location", "Status", "Source"]
    TABLE_COLS     = ["date_applied", "position", "company", "location", "status", "source"]

    def __init__(
        self,
        db: JobDatabase,
        section_name: str,
        section_label: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.db = db
        self.section_name = section_name
        self.section_label = section_label
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Search bar
        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(12)
        self.searchbar = QLineEdit()
        self.searchbar.setObjectName("searchBar")
        self.searchbar.setPlaceholderText("Search jobs by company, position, or location...")
        self.searchbar.setClearButtonEnabled(True)
        self.searchbar.textChanged.connect(self.update_jobs_displayed)
        self.searchbar.addAction(SearchIcon(), QLineEdit.ActionPosition.LeadingPosition)
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

        # Filter bar
        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(8)
        filter_row.addWidget(QLabel())

        filter_icon_label = QLabel()
        filter_icon_label.setPixmap(FilterIcon().pixmap(16, 16))
        filter_icon_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
            )
        filter_by_label = QLabel("Filter by:")
        filter_by_label.setObjectName("filterByLabel")
        filter_by_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        filter_row.addWidget(filter_icon_label)
        filter_row.addWidget(filter_by_label)

        self.status_filter = NoScrollComboBox()
        self.status_filter.setObjectName("filterCombo")
        self.status_filter.addItem("Any")
        self.status_filter.addItems(STATUS_OPTIONS)
        self.status_filter.setMinimumHeight(30)
        self.status_filter.currentTextChanged.connect(
            lambda _: self.update_jobs_displayed(self.searchbar.text())
        )
        filter_row.addWidget(QLabel("Status"))
        filter_row.addWidget(self.status_filter)
        filter_row.addWidget(self._make_separator())

        self.job_type_filter = NoScrollComboBox()
        self.job_type_filter.setObjectName("filterCombo")
        self.job_type_filter.addItem("Any")
        self.job_type_filter.addItems(JOB_TYPE_OPTIONS)
        self.job_type_filter.setMinimumHeight(30)
        self.job_type_filter.currentTextChanged.connect(
            lambda _: self.update_jobs_displayed(self.searchbar.text())
        )
        filter_row.addWidget(QLabel("Job type"))
        filter_row.addWidget(self.job_type_filter)
        filter_row.addWidget(self._make_separator())

        self.arrangement_filter = NoScrollComboBox()
        self.arrangement_filter.setObjectName("filterCombo")
        self.arrangement_filter.addItem("Any")
        self.arrangement_filter.addItems(WORK_ARRANGEMENT_OPTIONS)
        self.arrangement_filter.setMinimumHeight(30)
        self.arrangement_filter.currentTextChanged.connect(
            lambda _: self.update_jobs_displayed(self.searchbar.text())
        )
        filter_row.addWidget(QLabel("Arrangement"))
        filter_row.addWidget(self.arrangement_filter)
        filter_row.addWidget(self._make_separator())

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
        filter_row.addWidget(QLabel("Applied"))
        filter_row.addWidget(QLabel("from"))
        filter_row.addWidget(self.date_from_filter)
        filter_row.addWidget(QLabel("to"))
        filter_row.addWidget(self.date_to_filter)

        filter_row.addStretch(1)
        filter_row.addWidget(self._make_separator())
        sort_label = QLabel("Order by:")
        sort_label.setObjectName("filterByLabel")
        sort_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.sort_combo = NoScrollComboBox()
        self.sort_combo.setObjectName("filterCombo")
        self.sort_combo.addItems([
            "Date applied \u2193", "Date applied \u2191",
            "Last update \u2193",  "Last update \u2191",
        ])
        self.sort_combo.setMinimumHeight(30)
        self.sort_combo.currentTextChanged.connect(lambda _: self._sort_table())
        filter_row.addWidget(sort_label)
        filter_row.addWidget(self.sort_combo)
        layout.addLayout(filter_row)

        # Job table
        self.job_table = QTableWidget()
        self.job_table.setColumnCount(len(self.TABLE_HEADERS))
        self.job_table.setHorizontalHeaderLabels(self.TABLE_HEADERS)
        self.job_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.job_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.job_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.job_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.job_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.job_table.verticalHeader().setVisible(False)
        self.job_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.job_table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.job_table.setWordWrap(False)
        fm      = self.job_table.fontMetrics()
        padding = 24
        self.job_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.job_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.job_table.setColumnWidth(0, fm.horizontalAdvance("DD/MM/YYYY") + padding)
        self.job_table.setColumnWidth(4, fm.horizontalAdvance("Interview Scheduled") + padding)
        layout.addWidget(self.job_table)

        self.query_all_job_apps()
        self.populate_job_table()

    @staticmethod
    def _make_separator() -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setObjectName("filterSeparator")
        sep.setFixedWidth(1)
        sep.setMinimumHeight(20)
        return sep

    def populate_job_table(self):
        self.job_table.setRowCount(0)
        for job in self.job_applications:
            row = self.job_table.rowCount()
            self.job_table.insertRow(row)
            for col, key in enumerate(self.TABLE_COLS):
                item = QTableWidgetItem(job.get(key) or "")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, job)
                self.job_table.setItem(row, col, item)

    def query_all_job_apps(self):
        self.job_applications = self.db.get_all_jobs()
        self.job_companies  = [j["company"] for j in self.job_applications]
        self.job_positions  = [j["position"] for j in self.job_applications]
        self.job_locations  = [j["location"] for j in self.job_applications if j.get("location")]
        self.completer_hints = self.job_companies + self.job_positions + self.job_locations
        self.update_completer_hints(self.completer_hints)

    def update_jobs_displayed(self, text):
        t                    = (text or "").lower().strip()
        selected_status      = (self.status_filter.currentText() or "").strip()
        selected_job_type    = (self.job_type_filter.currentText() or "").strip()
        selected_arrangement = (self.arrangement_filter.currentText() or "").strip()
        date_from            = self.date_from_filter.date()
        date_to              = self.date_to_filter.date()
        no_lower_bound       = (date_from == QDate(2000, 1, 1))

        for row in range(self.job_table.rowCount()):
            job = self.job_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            matches_text = (
                not t
                or t in (job.get("company") or "").lower()
                or t in (job.get("position") or "").lower()
                or t in (job.get("location") or "").lower()
            )
            matches_status      = selected_status == "Any" or job["status"].strip() == selected_status
            matches_job_type    = selected_job_type == "Any" or (job.get("job_type") or "").strip() == selected_job_type
            matches_arrangement = selected_arrangement == "Any" or (job.get("work_arrangement") or "").strip() == selected_arrangement
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

    def get_selected_job(self):
        selected = self.job_table.selectedItems()
        if not selected:
            return None
        return self.job_table.item(selected[0].row(), 0).data(Qt.ItemDataRole.UserRole)

    def update_completer_hints(self, hints: list[str]):
        self.completer.setModel(QStringListModel(hints))

    def _sort_table(self):
        text = self.sort_combo.currentText()
        key_fn  = (lambda j: j.get("date_applied") or "") if "Date applied" in text else (lambda j: j.get("last_update") or "")
        reverse = "\u2193" in text
        self.job_applications.sort(key=key_fn, reverse=reverse)
        self.populate_job_table()
        self.update_jobs_displayed(self.searchbar.text())

    def refresh(self):
        self.query_all_job_apps()
        self.populate_job_table()
        self.update_jobs_displayed(self.searchbar.text())

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()


class CVEditorContainer(QWidget):
    back_to_list = pyqtSignal()

    def __init__(
        self,
        db: JobDatabase,
        paths: dict[str, Path],
        parent: QWidget | None = None,
        ) -> None:
        super().__init__(parent)

        self.db = db
        self.paths = paths
        self.section_defs = []
        self.cv_data = {}

    def load_cv_ui(self) -> None:
        self._teardown_ui()
        self._load_sections()
        self._build_ui()

    def _teardown_ui(self) -> None:
        existing_layout = self.layout()
        if existing_layout is not None:
            while existing_layout.count():
                item = existing_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            # Delete the layout itself
            QWidget().setLayout(existing_layout)

        # Reset state
        self.section_pages = {}
        self.section_defs = []
        self.current_cv = {}

    def _load_sections(self) -> None:
        if self.cv_data:
            # TODO: Handle when there is cv_data
            pass
        else:
            all_defs = load_section_names_from_yaml()
            cv_cfg = load_cv_config(self.paths.get("config"))
            order = cv_cfg.get("section_order")
            defs_by_name = {d["name"]: d for d in all_defs}
            self.section_defs = [defs_by_name[n] for n in order if n in defs_by_name]
            self.current_cv = cv_cfg.copy()
            self.section_defs = [sec for sec in self.section_defs if self.current_cv['sections'][sec['name']]['enabled']]
            self._section_defs_by_name = {d["name"]: d for d in self.section_defs}

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.top_nav = CVTopNavigator(self.section_defs, self)
        self.top_nav.back_clicked.connect(self.back_to_list.emit)
        self.top_nav.section_selected.connect(self._show_section)
        main_layout.addWidget(self.top_nav)

        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        self.section_pages: dict[str, QWidget] = {}

        self._create_target_app_page("target_application", "Target Application")
        for section_def in self.section_defs:
            self._create_section_page(section_def.get("name", ""))
        self._create_placeholder_page("reorder_sections", "Reorder Sections")
        self._create_placeholder_page("preview", "Preview CV")

        self._show_section("target_application")

    def _create_target_app_page(self, section_name: str, section_label: str) -> None:
        page = TargetApplicationPage(self.db, section_name, section_label, self)
        self.content_stack.addWidget(page)
        self.section_pages[section_name] = page

    def _create_section_page(self, section_name: str) -> None:
        section_def = self._section_defs_by_name.get(section_name)
        if section_def is None:
            raise ValueError(
                f"_create_section_page: no section_def found for {section_name!r}. "
                f"Ensure _load_sections() is called before _create_section_page()."
                )
        page = SectionSelectionPage(
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
        if section_name in self.section_pages:
            self.content_stack.setCurrentWidget(self.section_pages[section_name])
            self.top_nav.set_active_section(section_name)

    def set_cv_information(self, cv: Path | None = None) -> None:
        if cv is None:
            return

    def save_cv_information(self) -> None:
        return

    def get_current_cv(self) -> dict:
        return self.current_cv

    def update_current_cv(self, updated_cv: dict) -> None:
        self.current_cv = updated_cv


class CVBuilderPage(QWidget):

    def __init__(
        self,
        db: JobDatabase,
        paths: dict[str, Path],
        parent: QWidget | None = None,
        ):
        super().__init__(parent)
        self.db      = db
        self.paths   = paths

        self._build_ui()
        
        self._apply_stylesheet()

    def _build_ui(self) -> None:
        """Initializes the layout, creates widgets, and assembles the UI"""
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.subpages = QStackedWidget()
        self.layout.addWidget(self.subpages)

        self.main_page = CVListPage(self.db, self.paths, self)
        self.main_page.create_cv_clicked.connect(self._show_cv_editor)

        self.editor_container = CVEditorContainer(self.db, self.paths, self)
        # TODO: Delete all the information from the CVEditorContainer when returning to main list
        self.editor_container.back_to_list.connect(self._show_main_list)

        self.subpages.addWidget(self.main_page)
        self.subpages.addWidget(self.editor_container)

    def _show_main_list(self) -> None:
        self.subpages.setCurrentWidget(self.main_page)

    def _show_cv_editor(self, cv: Path | None = None) -> None:
        self.editor_container.set_cv_information(cv)
        self.editor_container.load_cv_ui()
        self.subpages.setCurrentWidget(self.editor_container)

    def _apply_stylesheet(self) -> None:
        """Apply consolidated stylesheet for all components."""
        window_bg = self.palette().color(QPalette.ColorRole.Window)
        text_color = self.palette().color(QPalette.ColorRole.WindowText)
        base_bg = self.palette().color(QPalette.ColorRole.Base)
        button_bg = self.palette().color(QPalette.ColorRole.Button)
        highlight = self.palette().color(QPalette.ColorRole.Highlight)
        
        dialog_bg = window_bg.lighter(110)
        border_color = window_bg.lighter(140)
        hover_bg = button_bg.lighter(120)
        stylesheet = f"""
            /* ==================== OVERLAY BACKGROUNDS ==================== */
            QWidget#overlay {{ background-color: rgba(0, 0, 0, 180); }}

            /* ======================= DIALOG FRAMES ======================= */
            QFrame#dialogFrame{{
                border-radius: 12px;
                border: 1px solid {border_color.name()};
                background-color: {dialog_bg.name()};
                }}
            
            
            QLabel {{ color: {text_color.name()}; }}
            QLineEdit, QTextEdit {{
                background-color: {base_bg.name()}; color: {text_color.name()};
                border: 1px solid {border_color.name()}; border-radius: 6px; padding: 6px;
            }}
            QLineEdit:focus, QTextEdit:focus {{ border: 1px solid {highlight.name()}; }}
            QComboBox {{ border: 1px solid {border_color.name()}; border-radius: 6px; padding: 6px; }}
            QPushButton {{
                background-color: {button_bg.name()}; color: {text_color.name()};
                border: 1px solid {border_color.name()} border-radius: 6px;
                padding: 8px 16px; font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {hover_bg.name()}; }}
            QPushButton#saveCurrentBtn {{ background-color: {highlight.name()}; border: 1px solid {highlight.name()}; }}
            QPushButton#saveCurrentBtn:hover {{ background-color: {highlight.darker(110).name()}; }}
            QPushButton#saveAllBtn {{ background-color: {highlight.name()}; border: 1px solid {highlight.name()}; }}
            QPushButton#saveAllBtn:hover {{ background-color: {highlight.darker(110).name()}; }}
            QPushButton#closeBtn {{
                background-color: transparent; border: none;
                font-size: 18px; padding: 4px 8px;
            }}
            QPushButton#closeBtn:hover {{ background-color: rgba(128,128,128,50); border-radius: 6px; }}
            QScrollArea {{ border: none; background-color: transparent; }}
            QGroupBox {{ border: 1px solid {border_color.name()}; border-radius: 8px; margin-top: 10px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 6px; }}
            """
        self.setStyleSheet(stylesheet)