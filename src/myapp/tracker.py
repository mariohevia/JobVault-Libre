from typing import Callable, Any

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QSizePolicy,
    QSpacerItem,
    QScrollArea,
    QLineEdit,
    QCompleter,
    QMessageBox,
    )

from PyQt6.QtCore import (
    Qt, 
    QStringListModel, 
    QEvent, 
    QDate,
    QObject,
    QTimer,
    )
from PyQt6.QtGui import QPalette, QShowEvent, QFontMetrics

from myapp.database import JobDatabase
from myapp.widgets import (
    NoScrollDateEdit, 
    NoScrollComboBox, 
    BaseColourTextEdit,
    )
from myapp.icons import (
    SearchIcon, 
    EditIcon, 
    FilterIcon,
    CloseIcon,
    DotsVerticalIcon,
    PencilPlusIcon,
    TrashIcon,
    DeselectIcon,
    SelectIcon,
    AlertIcon,
    )
from myapp.constants import (
    STATUS_OPTIONS, 
    STATUS_COLOURS, 
    JOB_TYPE_OPTIONS, 
    WORK_ARRANGEMENT_OPTIONS,
    EXTENSION_ONLY_DEFAULTS,
    )
from myapp.utils import JobDict, NewJobDict

# TODO: Decrease boilerplate in Overlays
# TODO: Handle cv and cover letter PDFs
class JobApplicationCard(QWidget):
    """
    Compact card widget representing a single job application.

    This widget displays high-level information about a job application
    (company, position, status, date applied, and location) in a
    card-style layout suitable for use inside list views or scroll areas.

    All job-related fields are stored as attributes on the instance,
    allowing the full application data to be accessed without additional
    database queries.
    """

    def __init__(
        self,
        job: JobDict,
        on_view: Callable[[JobDict], None],
        on_select_changed: Callable[[int, bool], None],
        ) -> None:

        super().__init__()
        self.on_view = on_view
        self.job = job
        self.on_select_changed = on_select_changed
        self.selected = False

        self.setMinimumWidth(400)
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
            )
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.setInterval(300)
        self._click_timer.timeout.connect(self._handle_single_click)

        self._build_ui()

    def _build_ui(self) -> None:
        # ── Outer frame and layouts ──────────────────────────────────────────
        self.frame = QFrame(self)
        self.frame.setObjectName("cardFrame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.frame)

        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # ── Top row  ─────────────────────────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.company_label = QLabel(self.job["company"])
        self.company_label.setObjectName("companyLabel")
        self.company_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.status_badge = QLabel(self.job["status"])
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setContentsMargins(8, 2, 8, 2)
        status_badge_color = STATUS_COLOURS.get(self.job["status"], "#6B7280")

        self.status_badge.setStyleSheet(f"""
            QLabel#statusBadge {{
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 11px;
                color: #ffffff;
                background-color: {status_badge_color};
                }}
                """)

        top_row.addWidget(self.company_label)
        top_row.addStretch()
        top_row.addWidget(self.status_badge)

        layout.addLayout(top_row)

        # ── Middle row  ──────────────────────────────────────────────────────
        self.position_label = QLabel(self.job["position"])
        self.position_label.setObjectName("positionLabel")

        if self.job["date_applied"]:
            date = QDate.fromString(self.job["date_applied"], Qt.DateFormat.ISODate)
            date_text = f"Applied: {date.toString('dd/MM/yyyy')}"
        else:
            date_text = "Not applied"
        self.date_label = QLabel(date_text)
        self.date_label.setObjectName("dateLabel")

        middle_row = QHBoxLayout()
        middle_row.setSpacing(8)
        middle_row.addWidget(self.position_label)
        middle_row.addStretch()
        middle_row.addWidget(self.date_label)

        layout.addLayout(middle_row)

        # ── Bottom row  ──────────────────────────────────────────────────────
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self.location_label = QLabel(self.job["location"] or "")
        self.location_label.setObjectName("locationLabel")

        bottom_row.addWidget(self.location_label)
        bottom_row.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.details_button = QPushButton()
        self.details_button.setIcon(DotsVerticalIcon())
        self.details_button.setObjectName("detailsButton")
        self.details_button.setFixedSize(32, 32)
        self.details_button.clicked.connect(self._handle_view_clicked)
        bottom_row.addWidget(self.details_button)

        layout.addLayout(bottom_row)

    def _handle_view_clicked(self) -> None:
        self.on_view(self.job)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._click_timer.start()  # defer the "select" action
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def _handle_single_click(self):
        self.set_selected(not self.selected)
        self.on_select_changed(int(self.job["id"]), self.selected)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._click_timer.stop()
            self.on_view(self.job)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def set_selected(self, selected: bool):
        self.selected = selected
        self.frame.setProperty("selected", selected)

        # Force Qt to recalculate styles
        self.frame.style().unpolish(self.frame)
        self.frame.style().polish(self.frame)
        self.frame.update()

class BaseOverlay(QWidget):
    """
    Base class for full-parent overlays with a centred dialog panel.
 
    Subclasses must implement `_build_form`, which receives the
    `scroll_layout` (a `QVBoxLayout` inside the scrollable area) and
    should populate it with form content.
 
    The title row always contains a title label and a close button.
    Extra buttons (e.g. an Edit icon) can be injected before the close
    button by overriding `_title_row_extra_buttons` and returning
    a list of `QPushButton` instances.
 
    Action buttons (Save, Cancel, Delete) sit below the scroll area in a
    non-scrollable row.  Override `_build_action_buttons` and add
    widgets to the supplied `QHBoxLayout`.
 
    Closing behaviour (X button, Escape key, click-outside) is handled here
    and works identically for every subclass.
    """
    def __init__(self, parent: QWidget, title: str) -> None:
        super().__init__(parent)
        self._title_text = title
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setObjectName("Overlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.installEventFilter(self)

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the fixed outer structure: backdrop -> dialog -> sections."""
        # ── Outer frame and layouts ──────────────────────────────────────────
        self.dialog = QFrame(self)
        self.dialog.setObjectName("dialogFrame")
        self.dialog.setMinimumSize(200, 500)

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

        close_btn = QPushButton("")
        close_btn.setIcon(CloseIcon())
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(32, 32)

        title_row.addWidget(title_label)
        title_row.addStretch()
        for btn in self._title_row_extra_buttons():
            title_row.addWidget(btn)
        title_row.addWidget(close_btn)

        dialog_layout.addLayout(title_row)

        # ── Form (scrollable) ────────────────────────────────────────────────
        scroll_area = QScrollArea()
        scroll_area.setObjectName("dialogScroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
            )

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 8, 0)
        scroll_layout.setSpacing(10)

        scroll_area.setWidget(scroll_content)

        self._build_form(scroll_layout)
        dialog_layout.addWidget(scroll_area, stretch=1)

        # ── Action buttons (NOT scrollable) ──────────────────────────────────
        actions = QHBoxLayout()
        actions.addStretch()
        self._build_action_buttons(actions)
        dialog_layout.addLayout(actions)

    def _title_row_extra_buttons(self) -> list[QPushButton]:
        """
        Return extra buttons inserted between the title label and the close
        button.  Default: no extra buttons.
        """
        return []

    def _build_form(self, scroll_layout: QVBoxLayout) -> None:
        """
        Populate the scrollable area.  Called once during `__init__`.
        Subclasses must override this.
        """
        raise NotImplementedError

    def _build_action_buttons(self, actions: QHBoxLayout) -> None:
        """
        Add action buttons to the pre-stretched `actions` layout.
        Default: no buttons (overlay only has the close button in the title).
        """
        return

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
        """Close overlay on Escape."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    @staticmethod
    def _make_form() -> tuple[QGridLayout, Qt.AlignmentFlag, Qt.AlignmentFlag]:
        """
        Return a configured QGridLayout plus the two standard label alignments.
        """
        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        label_alignment = (
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
        label_alignment_top = (
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
            )
        return form, label_alignment, label_alignment_top

    @staticmethod
    def _add_pair(
        form: QGridLayout,
        row: int,
        left_label: QLabel,
        left_widget: QWidget,
        right_label: QLabel,
        right_widget: QWidget,
        alignment: Qt.AlignmentFlag,
        ) -> None:
        form.addWidget(left_label, row, 0, alignment=alignment)
        form.addWidget(left_widget, row, 1)
        form.addWidget(right_label, row, 2, alignment=alignment)
        form.addWidget(right_widget, row, 3)

    @staticmethod
    def _add_single(
        form: QGridLayout,
        row: int,
        label: QLabel,
        widget: QWidget,
        alignment: Qt.AlignmentFlag,
        ) -> None:
        form.addWidget(label, row, 0, alignment=alignment)
        form.addWidget(widget, row, 1, 1, 3)

    @staticmethod
    def _create_label(text: str, required: bool = False) -> QLabel:
        """Return a form label with an optional required (*) marker."""
        return QLabel(f"{text} *" if required else text)

    @staticmethod
    def _connect_status(
        status_combo: NoScrollComboBox,
        date_widget: NoScrollDateEdit,
        ) -> None:
        """Wire up the status combo so it enables/disables the date widget."""
    
        def on_status_changed(text: str) -> None:
            is_not_applied = text == "Not Applied"
            if is_not_applied:
                date_widget.setSpecialValueText(" ")
                date_widget.setDate(date_widget.minimumDate())
                date_widget.setEnabled(False)
            else:
                date_widget.setSpecialValueText("")
                if date_widget.date() == date_widget.minimumDate():
                    date_widget.setDate(QDate.currentDate())
                date_widget.setEnabled(True)
    
        status_combo.currentTextChanged.connect(on_status_changed)

    @staticmethod
    def _connect_work_arrangement(
        arrangement_combo: NoScrollComboBox,
        office_days_combo: NoScrollComboBox,
        ) -> None:
        """Wire up the arrangement combo so it enables/disables office-days."""

        def on_arrangement_changed(text: str) -> None:
            is_hybrid = text == "Hybrid"
            office_days_combo.setEnabled(is_hybrid)
            if is_hybrid:
                idx = office_days_combo.findText("N/A")
                office_days_combo.removeItem(idx)
                office_days_combo.setCurrentIndex(0)
            else:
                if office_days_combo.findText("N/A") == -1:
                    office_days_combo.addItem("N/A")
                idx = office_days_combo.findText("N/A")
                office_days_combo.setCurrentIndex(idx)
    
        arrangement_combo.currentTextChanged.connect(on_arrangement_changed)

    @staticmethod
    def _parse_office_days(text: str) -> int | None:
        if text == "N/A":
            return None
        if text == "Not specified":
            return 0
        return int(text)

    @staticmethod
    def _validate_required(
        field: QLineEdit,
        error_style: str,
        base_style: str,
    ) -> bool:
        """Apply error/base styling and return True when the field is non-empty."""
        if not field.text().strip():
            field.setStyleSheet(error_style)
            return False
        field.setStyleSheet(base_style)
        return True


class AddApplicationOverlay(BaseOverlay):
    """
    An in-window overlay (covers parent) to add a job application
    The overlay closes when:
    - pressing the X button
    - pressing the Cancel button
    - clicking outside the popup panel
    - pressing Escape
    """

    _ERROR_STYLE = "border: 2px solid #dc3545 !important;"
    _BASE_STYLE = ""

    def __init__(
        self,
        parent: QWidget,
        on_submit: Callable[[NewJobDict], None],
        ) -> None:
        self.on_submit = on_submit
        super().__init__(
            parent, 
            title="Add Application",
            )

    def _build_form(self, scroll_layout: QVBoxLayout) -> None:
        form, label_align, label_align_top = self._make_form()

        self.company = QLineEdit()
        self.company.setObjectName("formInput")
        self.company.setPlaceholderText("e.g., Google")

        self.position = QLineEdit()
        self.position.setObjectName("formInput")
        self.position.setPlaceholderText("e.g., Software Engineer")

        self.status = NoScrollComboBox()
        self.status.setObjectName("formCombo")
        self.status.addItems(STATUS_OPTIONS)
        self.status.setCurrentIndex(1)
        self.status.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

        self.date_applied = NoScrollDateEdit()
        self.date_applied.setObjectName("formDate")
        self._connect_status(self.status, self.date_applied)

        self.job_type = NoScrollComboBox()
        self.job_type.setObjectName("formCombo")
        self.job_type.addItems(JOB_TYPE_OPTIONS)
        self.job_type.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

        self.work_arrangement = NoScrollComboBox()
        self.work_arrangement.setObjectName("formCombo")
        self.work_arrangement.addItems(WORK_ARRANGEMENT_OPTIONS)
        self.work_arrangement.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

        self.office_days = NoScrollComboBox()
        self.office_days.addItems(
            ["N/A", "Not specified"]+[str(i) for i in range(1,5)]
            )
        self.office_days.setObjectName("formCombo")
        self.office_days.setEnabled(False)
        self._connect_work_arrangement(self.work_arrangement, self.office_days)
        self.office_days.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

        self.location = QLineEdit()
        self.location.setObjectName("formInput")
        self.location.setPlaceholderText("e.g., London, UK")

        self.source = QLineEdit()
        self.source.setObjectName("formInput")
        self.source.setPlaceholderText("e.g., LinkedIn")

        self.salary_range = QLineEdit()
        self.salary_range.setObjectName("formInput")
        self.salary_range.setPlaceholderText("e.g., £100k - £150k")

        self.contact_name = QLineEdit()
        self.contact_name.setObjectName("formInput")
        self.contact_name.setPlaceholderText("Recruiter name")

        self.contact_email = QLineEdit()
        self.contact_email.setObjectName("formInput")
        self.contact_email.setPlaceholderText("email@company.com")

        self.company_website = QLineEdit()
        self.company_website.setObjectName("formInput")
        self.company_website.setPlaceholderText("https://...")

        self.job_url = QLineEdit()
        self.job_url.setObjectName("formInput")
        self.job_url.setPlaceholderText("https://...")

        self.job_description = BaseColourTextEdit()
        self.job_description.setObjectName("formTextEdit")
        self.job_description.setPlaceholderText(
            "Paste job description here..."
            )
        self.job_description.setAcceptRichText(True)
        self.job_description.setFixedHeight(150)
        
        self.notes = BaseColourTextEdit()
        self.notes.setObjectName("formTextEdit")
        self.notes.setPlaceholderText("Additional notes...")
        self.notes.setAcceptRichText(True)
        self.notes.setFixedHeight(150)

        pairs = [
            (
                ("Job title", True), self.position,
                ("Company", True), self.company
            ),
            (
                ("Date applied", False), self.date_applied, 
                ("Status", True), self.status
            ),
            (
                ("Job location", False), self.location, 
                ("Job type", False), self.job_type
            ),
            (
                ("Job source", False), self.source, 
                ("Salary range", False), self.salary_range
            ),
            (
                ("Work arrangment", False), self.work_arrangement, 
                ("Office days", False), self.office_days
            ),
            (
                ("Contact name", False), self.contact_name, 
                ("Contact email", False), self.contact_email
            ),
            ]
        for row, (l_meta, l_widget, r_meta, r_widget) in enumerate(pairs):
            self._add_pair(
                form, row,
                self._create_label(*l_meta), l_widget,
                self._create_label(*r_meta), r_widget,
                label_align,
                )

        singles = [
            ("Job URL", self.job_url, label_align),
            ("Company website", self.company_website, label_align),
            ("Job description", self.job_description, label_align_top),
            ("Notes", self.notes, label_align_top),
            ]
        for offset, (text, widget, align) in enumerate(singles):
            self._add_single(
                form, 
                len(pairs) + offset, 
                QLabel(text), 
                widget, 
                align
                )

        scroll_layout.addLayout(form)

    def _build_action_buttons(self, actions: QHBoxLayout) -> None:
        cancel = QPushButton("Cancel")
        cancel.setObjectName("cancelBtn")
        cancel.clicked.connect(self.close)
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setFixedHeight(36)

        save = QPushButton("Save")
        save.setObjectName("saveBtn")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.clicked.connect(self._submit)
        save.setFixedHeight(36)

        actions.addWidget(cancel)
        actions.addSpacing(8)
        actions.addWidget(save)

    def _on_show(self) -> None:
        self.position.setFocus()

    def _submit(self) -> None:
        """Validate and submit the form."""
        valid = all([
            self._validate_required(
                self.company, 
                self._ERROR_STYLE, 
                self._BASE_STYLE
                ),
            self._validate_required(
                self.position, 
                self._ERROR_STYLE, 
                self._BASE_STYLE
                ),
            ])
        if not valid:
            return

        status = self.status.currentText().strip()
        office_days = self._parse_office_days(
            self.office_days.currentText().strip()
            )
        if status == "Not Applied":
            date_applied_value = None
        else:
            date_applied_value = self.date_applied.date().toString(
                Qt.DateFormat.ISODate) or None
        payload = NewJobDict({
            "company": self.company.text().strip(),
            "position": self.position.text().strip(),
            "status": status,
            "work_arrangement": self.work_arrangement.currentText().strip(),
            "office_days": office_days,
            "company_website": self.company_website.text().strip() or None,
            "location": self.location.text().strip() or None,
            "source": self.source.text().strip() or None,
            "job_type": self.job_type.currentText().strip(),
            "date_applied": date_applied_value,
            "contact_name": self.contact_name.text().strip() or None,
            "contact_email": self.contact_email.text().strip() or None,
            "salary_range": self.salary_range.text().strip() or None,
            "job_url": self.job_url.text().strip() or None,
            "job_description": self.job_description.toHtml().strip() or None,
            "notes": self.notes.toHtml().strip() or None,
            "cv_pdf": None,
            "cv_text": None,
            "cover_letter_pdf": None,
            "cover_letter_text": None,
            })

        self.on_submit(payload)
        self.close()


class ViewApplicationOverlay(BaseOverlay):
    """
    In-window overlay (covers parent) to view a job application
    The overlay closes when:
    - pressing the X button
    - pressing the Close button
    - clicking outside the popup panel
    - pressing Escape

    Shows all values (read-only) and provides Edit and Remove buttons.
    """
    def __init__(
        self,
        parent: QWidget,
        job: JobDict,
        on_remove: Callable[[int], None],
        on_edit: Callable[[JobDict], None],
        ) -> None:
        self.job = JobDict(job)
        self.on_remove = on_remove
        self.on_edit = on_edit
        super().__init__(
            parent, 
            title="Application Details",
            )

    def _title_row_extra_buttons(self) -> list[QPushButton]:
        edit_btn = QPushButton("")
        edit_btn.setIcon(EditIcon())
        edit_btn.setObjectName("editBtn")
        edit_btn.setToolTip("Edit application")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(self._open_edit_overlay)
        edit_btn.setFixedSize(32, 32)
        return [edit_btn]

    def _build_form(self, scroll_layout: QVBoxLayout) -> None:
        form, label_align, label_align_top = self._make_form()

        def make_value_label(key: str) -> QLabel:
            value = self.job[key]
            if value == 0:
                value = "Not specified"
            elif value is None or value == "":
                value = "—"
            elif isinstance(value, str):
                date = QDate.fromString(value, Qt.DateFormat.ISODate)
                if date.isValid():
                    value = date.toString("dd/MM/yyyy")
            value_label = QLabel(str(value))
            value_label.setObjectName("valueLabel")
            value_label.setSizePolicy(
                QSizePolicy.Policy.Expanding, 
                QSizePolicy.Policy.Minimum
                )
            value_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
                | Qt.TextInteractionFlag.TextSelectableByKeyboard
                )
            value_label.setCursor(Qt.CursorShape.IBeamCursor)
            value_label.setWordWrap(True)
            return value_label

        pairs = [
            ("Job title", "position", 
             "Company", "company"),
            ("Date applied", "date_applied", 
             "Status", "status"),
            ("Job location", "location", 
             "Job type", "job_type"),
            ("Job source", "source", 
             "Salary range", "salary_range"),
            ("Work arrangment", "work_arrangement", 
             "Office days", "office_days"),
            ("Contact name", "contact_name", 
             "Contact email", "contact_email"),
        ]

        for row, (l_text, l_key, r_text, r_key) in enumerate(pairs):
            self._add_pair(
                form, row,
                QLabel(l_text), make_value_label(l_key),
                QLabel(r_text), make_value_label(r_key),
                label_align,
            )

        singles = [
            ("Job URL", "job_url", label_align),
            ("Company website", "company_website", label_align),
            ("Job description", "job_description", label_align_top),
            ("Notes", "notes", label_align_top),
            ("Last update", "last_update", label_align),
            ]
        for offset, (text, key, align) in enumerate(singles):
            self._add_single(
                form, 
                len(pairs) + offset, 
                QLabel(text), 
                make_value_label(key), 
                align
                )

        scroll_layout.addLayout(form)
        scroll_layout.addStretch(1)

    def _build_action_buttons(self, actions: QHBoxLayout) -> None:
        close = QPushButton("Close")
        close.setObjectName("cancelBtn")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(self.close)
        close.setFixedHeight(36)

        remove = QPushButton("Delete")
        remove.setObjectName("removeBtn")
        remove.setCursor(Qt.CursorShape.PointingHandCursor)
        remove.clicked.connect(self._remove)
        remove.setFixedHeight(36)

        actions.addWidget(close)
        actions.addSpacing(8)
        actions.addWidget(remove)

    def _open_edit_overlay(self) -> None:
        """Invokes the edit callback and closes the current dialog."""
        self.on_edit(self.job)
        self.close()

    def _remove(self) -> None:
        """
        Confirms deletion with the user and triggers the removal callback by
        job ID.
        """
        pos = self.job['position']
        pos_text = f" {pos}" if pos else "this position"
        org = self.job['company']
        org_text = f" at {org}?" if org else "?"
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete the application for"
            f" {pos_text}{org_text}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        if reply == QMessageBox.StandardButton.Yes:
            job_id = self.job["id"]
            self.on_remove(int(job_id))
            self.close()


class EditApplicationOverlay(BaseOverlay):
    """
    An in-window overlay (covers parent) to edit a job application
    The overlay closes when:
    - pressing the X button
    - pressing the Cancel button
    - clicking outside the popup panel
    - pressing Escape
    """

    _ERROR_STYLE = "border: 2px solid #dc3545 !important;"
    _BASE_STYLE = ""

    def __init__(
        self, 
        parent: QWidget, 
        job: JobDict, 
        on_save: Callable[dict[Any], None], 
        on_remove: Callable[[int], None], 
        ) -> None:
        self.job = JobDict(job)
        self.on_save = on_save
        self.on_remove = on_remove
        super().__init__(
            parent, 
            title="Edit Application",
            )

    def _build_form(self, scroll_layout: QVBoxLayout) -> None:
        form, label_align, label_align_top = self._make_form()

        self.company = QLineEdit(self.job["company"])
        self.company.setObjectName("formInput")
        self.company.setPlaceholderText("e.g., Google")

        self.position = QLineEdit(self.job["position"])
        self.position.setObjectName("formInput")
        self.position.setPlaceholderText("e.g., Software Engineer")

        self.status = NoScrollComboBox()
        self.status.setObjectName("formCombo")
        self.status.addItems(STATUS_OPTIONS)
        idx = self.status.findText((self.job["status"] or "").strip())
        self.status.setCurrentIndex(idx if idx >= 0 else 0)
        self.status.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

        existing_date_str = self.job["date_applied"] or ""
        date = QDate.fromString(existing_date_str, Qt.DateFormat.ISODate)
        self.date_applied = NoScrollDateEdit(
            date=date if date.isValid() else None
            )
        self.date_applied.setObjectName("formDate")
        self._connect_status(self.status, self.date_applied)

        self.job_type = NoScrollComboBox()
        self.job_type.setObjectName("formCombo")
        self.job_type.addItems(JOB_TYPE_OPTIONS)
        idx = self.job_type.findText((self.job["job_type"] or "").strip())
        self.job_type.setCurrentIndex(idx if idx >= 0 else 0)
        self.job_type.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

        self.work_arrangement = NoScrollComboBox()
        self.work_arrangement.setObjectName("formCombo")
        self.work_arrangement.addItems(WORK_ARRANGEMENT_OPTIONS)
        current_work_arrangement = (
            self.job["work_arrangement"] or ""
            ).strip()
        idx = self.work_arrangement.findText(current_work_arrangement)
        self.work_arrangement.setCurrentIndex(idx if idx >= 0 else 0)
        self.work_arrangement.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

        self.office_days = NoScrollComboBox()
        self.office_days.setObjectName("formCombo")
        current_office_days = self.job["office_days"]
        if current_office_days is None:
            self.office_days.addItems(
                ["N/A", "Not specified"]+[str(i) for i in range(1,5)]
                )
            self.office_days.setEnabled(False)
        else:
            self.office_days.addItems(
                ["Not specified"]+[str(i) for i in range(1,5)]
                )
            self.office_days.setCurrentIndex(current_office_days)
        self._connect_work_arrangement(self.work_arrangement, self.office_days)
        self.office_days.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

        self.location = QLineEdit(self.job["location"] or "")
        self.location.setObjectName("formInput")
        self.location.setPlaceholderText("e.g., London, UK")

        self.source = QLineEdit(self.job["source"] or "")
        self.source.setObjectName("formInput")
        self.source.setPlaceholderText("e.g., LinkedIn")

        self.salary_range = QLineEdit(self.job["salary_range"] or "")
        self.salary_range.setObjectName("formInput")
        self.salary_range.setPlaceholderText("e.g., £100k - £150k")

        self.contact_name = QLineEdit(self.job["contact_name"] or "")
        self.contact_name.setObjectName("formInput")
        self.contact_name.setPlaceholderText("Recruiter name")

        self.contact_email = QLineEdit(self.job["contact_email"] or "")
        self.contact_email.setObjectName("formInput")
        self.contact_email.setPlaceholderText("email@company.com")

        self.company_website = QLineEdit(self.job["company_website"] or "")
        self.company_website.setObjectName("formInput")
        self.company_website.setPlaceholderText("https://...")

        self.job_url = QLineEdit(self.job["job_url"] or "")
        self.job_url.setObjectName("formInput")
        self.job_url.setPlaceholderText("https://...")

        self.job_description = BaseColourTextEdit()
        self.job_description.setObjectName("formTextEdit")
        self.job_description.setPlaceholderText(
            "Paste job description here..."
            )
        self.job_description.setAcceptRichText(True)
        self.job_description.setHtml(self.job["job_description"] or "")
        self.job_description.setFixedHeight(150)

        self.notes = BaseColourTextEdit()
        self.notes.setObjectName("formTextEdit")
        self.notes.setPlaceholderText("Additional notes...")
        self.notes.setAcceptRichText(True)
        self.notes.setHtml(self.job["notes"] or "")
        self.notes.setFixedHeight(150)

        pairs = [
            (
                ("Job title", True), self.position,
                ("Company", True), self.company
            ),
            (
                ("Date applied", False), self.date_applied, 
                ("Status", True), self.status
            ),
            (
                ("Job location", False), self.location, 
                ("Job type", False), self.job_type
            ),
            (
                ("Job source", False), self.source, 
                ("Salary range", False), self.salary_range
            ),
            (
                ("Work arrangment", False), self.work_arrangement, 
                ("Office days", False), self.office_days
            ),
            (
                ("Contact name", False), self.contact_name, 
                ("Contact email", False), self.contact_email
            ),
            ]
        for row, (l_meta, l_widget, r_meta, r_widget) in enumerate(pairs):
            self._add_pair(
                form, row,
                self._create_label(*l_meta), l_widget,
                self._create_label(*r_meta), r_widget,
                label_align,
                )

        singles = [
            ("Job URL", self.job_url, label_align),
            ("Company website", self.company_website, label_align),
            ("Job description", self.job_description, label_align_top),
            ("Notes", self.notes, label_align_top),
            ]
        for offset, (text, widget, align) in enumerate(singles):
            self._add_single(
                form, 
                len(pairs) + offset, 
                QLabel(text), 
                widget, 
                align
                )

        scroll_layout.addLayout(form)

    def _build_action_buttons(self, actions: QHBoxLayout) -> None:
        cancel = QPushButton("Cancel")
        cancel.setObjectName("cancelBtn")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.close)
        cancel.setFixedHeight(36)

        remove = QPushButton("Delete")
        remove.setObjectName("removeBtn")
        remove.setCursor(Qt.CursorShape.PointingHandCursor)
        remove.clicked.connect(self._remove)
        remove.setFixedHeight(36)

        save = QPushButton("Save")
        save.setObjectName("saveBtn")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.clicked.connect(self._save)
        save.setFixedHeight(36)

        actions.addWidget(cancel)
        actions.addSpacing(8)
        actions.addWidget(remove)
        actions.addSpacing(8)
        actions.addWidget(save)

    def _on_show(self) -> None:
        self.position.setFocus()

    def _remove(self) -> None:
        """
        Confirms deletion with the user and triggers the removal callback by
        job ID.
        """
        pos = self.job['position']
        pos_text = f" {pos}" if pos else "this position"
        org = self.job['company']
        org_text = f" at {org}?" if org else "?"
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete the application for"
            f" {pos_text}{org_text}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        if reply == QMessageBox.StandardButton.Yes:
            job_id = self.job["id"]
            self.on_remove(int(job_id))
            self.close()

    def _save(self) -> None:
        valid = all([
            self._validate_required(
                self.company, 
                self._ERROR_STYLE, 
                self._BASE_STYLE
                ),
            self._validate_required(
                self.position, 
                self._ERROR_STYLE, 
                self._BASE_STYLE
                ),
            ])
        if not valid:
            return

        status = self.status.currentText().strip()
        office_days = self._parse_office_days(
            self.office_days.currentText().strip()
            )
        if status == "Not Applied":
            date_applied_value = None
        else:
            date_applied_value = (
                self.date_applied.date().toString(Qt.DateFormat.ISODate)
                or None
                )

        current = JobDict({
            "id": self.job["id"],
            "company": self.company.text().strip(),
            "position": self.position.text().strip(),
            "status": status,
            "work_arrangement": self.work_arrangement.currentText().strip(),
            "office_days": office_days,
            "company_website": self.company_website.text().strip() or None,
            "location": self.location.text().strip() or None,
            "source": self.source.text().strip() or None,
            "job_type": self.job_type.currentText().strip(),
            "date_applied": date_applied_value,
            "contact_name": self.contact_name.text().strip() or None,
            "contact_email": self.contact_email.text().strip() or None,
            "salary_range": self.salary_range.text().strip() or None,
            "job_url": self.job_url.text().strip() or None,
            "job_description": self.job_description.toHtml().strip() or None,
            "notes": self.notes.toHtml().strip() or None,
            # TODO: Handle cv and coverletter data
            "cv_pdf": None,
            "cv_text": None,
            "cover_letter_pdf": None,
            "cover_letter_text": None,
            })

        changes = {}
        for k, new_v in current.items():
            if k == "id":
                continue
            old_v = self.job[k]
            if new_v != old_v:
                changes[k] = new_v

        if changes:
            self.on_save(int(self.job["id"]), changes)

        self.close()

class BulkDeleteOverlay(QWidget):
    def __init__(
        self,
        parent: QWidget,
        jobs: list[JobDict],
        on_delete: Callable[[list[JobDict]], None],
    ):
        super().__init__(parent)

        self.jobs = jobs
        self.on_delete = on_delete

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setObjectName("Overlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(60, 40, 60, 80)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dialog = QFrame()
        self.dialog.setObjectName("dialogFrame")

        # Fixed vertical size
        self.dialog.setFixedHeight(420)

        root_layout.addWidget(self.dialog)

        dialog_layout = QVBoxLayout(self.dialog)
        dialog_layout.setContentsMargins(24, 20, 24, 20)
        dialog_layout.setSpacing(12)

        # Title row
        title_row = QHBoxLayout()
        count = len(self.jobs)
        title = QLabel(
            f"Delete {count} application{'s' if count != 1 else ''}?"
        )
        title.setObjectName("dialogTitle")
        warning_text = QLabel("This action cannot be undone.")
        warning_text.setObjectName("warningLabel")

        alert_icon_label = QLabel()
        alert_icon_label.setPixmap(AlertIcon(color_name="#DC6363").pixmap(16, 16))
        alert_icon_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
            )

        close = QPushButton()
        close.setIcon(CloseIcon())
        close.setObjectName("closeBtn")
        close.setFixedSize(32, 32)
        close.clicked.connect(self.close)

        title_row.addWidget(title)
        title_row.addWidget(alert_icon_label)
        title_row.addWidget(warning_text)
        title_row.addStretch()
        title_row.addWidget(close)

        dialog_layout.addLayout(title_row)
        
        # Job list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        content_layout = QGridLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setHorizontalSpacing(16)
        content_layout.setVerticalSpacing(8)

        row_idx = 0
        for i, job in enumerate(self.jobs):
            position = QLabel(job['position'])
            position.setObjectName("jobPosition")

            company = QLabel(job['company'])
            company.setObjectName("jobCompany")

            date = QLabel(job['date_applied'] or 'Not applied')
            date.setObjectName("jobDate")

            status = QLabel(job['status'])
            status.setObjectName("jobStatus")

            content_layout.addWidget(position, row_idx, 0)
            content_layout.addWidget(company, row_idx, 2)
            content_layout.addWidget(date, row_idx, 3)
            content_layout.addWidget(status, row_idx, 4)
            row_idx += 1

            if i < len(self.jobs) - 1:
                row_idx += 1

        content_layout.setColumnStretch(0, 1)
        content_layout.setColumnStretch(1, 1)
        content_layout.setColumnStretch(2, 1)
        content_layout.setColumnStretch(3, 1)
        content_layout.setRowStretch(row_idx, 1)

        scroll.setWidget(content)

        dialog_layout.addWidget(scroll)

        # Buttons
        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel = QPushButton("Cancel")
        cancel.setObjectName("cancelBtn")
        cancel.clicked.connect(self.close)

        delete = QPushButton(
            f"Delete {len(self.jobs)} application{'s' if count != 1 else ''}"
        )
        delete.setObjectName("removeBtn")
        delete.clicked.connect(self._delete)

        buttons.addWidget(cancel)
        buttons.addSpacing(8)
        buttons.addWidget(delete)

        dialog_layout.addLayout(buttons)

    def _delete(self):
        self.on_delete(self.jobs)
        self.close()

    def showEvent(self, event):
        super().showEvent(event)
        self._fit_to_parent()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_to_parent()

    def _fit_to_parent(self):
        parent = self.parentWidget()

        if parent:
            self.setGeometry(parent.rect())
            width = int(parent.width() * 0.55)
            self.dialog.setFixedWidth(width)

class TrackerPage(QWidget):

    ROWS_COMPLETER = 3
    # Sentinel Julian day used for "Not Applied" jobs in sort (treated as newer
    # than any real date)
    _SORT_SENTINEL_NOT_APPLIED = 99999999
    
    def __init__(
        self, 
        db: JobDatabase, 
        parent: QWidget | None = None
        ) -> None:
        
        super().__init__(parent)
        self.db = db
        self.job_applications = []
        self.job_card_widgets = []
        self._overlay = None

        self._build_ui()
        
        self._apply_stylesheet()

        self.refresh_from_db()
        
        self.selected_job_ids = set()
        self.update_selection_bar()
        self.parent = parent

    def _build_ui(self) -> None:
        """Initializes the layout, creates widgets, and assembles the UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)

        # ── Row 1: Search bar + Add button ───────────────────────────────────
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
            SearchIcon(),
            QLineEdit.ActionPosition.LeadingPosition
            )

        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.searchbar.setCompleter(self.completer)
        popup = self.completer.popup()
        popup.setObjectName("completerPopup")
        popup.setUniformItemSizes(True)
        popup.setMaximumHeight(
            ((self.searchbar.fontMetrics().height() + 4 + 8)
             * self.ROWS_COMPLETER + 2)
            )
        #TODO: Set this stylesheet at the app level
        popup.setStyleSheet("""
            /* ==================== COMPLETER POPUP ==================== */
            QListView#completerPopup {
                border: 1px solid palette(mid);
                border-radius: 2px;
                padding: 4px;
                }
            QListView#completerPopup::item {
                padding: 4px;
                }
            QListView#completerPopup::item:selected {
                border-radius: 2px;
                background-color: palette(highlight);
                color: palette(highlighted-text);
                }
            QListView#completerPopup::item:hover {
                border-radius: 2px;
                background-color: palette(highlight);
                color: palette(highlighted-text);
                }
            """)

        self.add_application_button = QPushButton(" Add Application")
        self.add_application_button.setIcon(
            PencilPlusIcon(color_role=QPalette.ColorRole.HighlightedText)
            )
        self.add_application_button.setObjectName("addApplicationButton")
        self.add_application_button.clicked.connect(self.add_application)
        self.add_application_button.setCursor(
            Qt.CursorShape.PointingHandCursor
            )
        self.add_application_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
            )
        self.add_application_button.setMinimumHeight(34)

        search_row.addWidget(self.add_application_button)
        search_row.addWidget(self.searchbar, stretch=1)

        main_layout.addLayout(search_row)

        # ── Row 2: Filter bar ────────────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(8)

        filter_icon_label = QLabel()
        filter_icon_label.setPixmap(FilterIcon().pixmap(16, 16))
        filter_icon_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
            )
        filter_by_label = QLabel("Filter by:")
        filter_by_label.setObjectName("filterByLabel")
        filter_by_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

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
        self.status_filter.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

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
        self.job_type_filter.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

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
        self.arrangement_filter.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

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
            lambda _: self._sort_cards()
            )
        self.sort_combo.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

        filter_row.addWidget(filter_icon_label)
        filter_row.addWidget(filter_by_label)
        filter_row.addWidget(status_label)
        filter_row.addWidget(self.status_filter)
        filter_row.addSpacing(8)
        filter_row.addWidget(self._make_separator())
        filter_row.addSpacing(8)
        filter_row.addWidget(job_type_label)
        filter_row.addWidget(self.job_type_filter)
        filter_row.addSpacing(8)
        filter_row.addWidget(self._make_separator())
        filter_row.addSpacing(8)
        filter_row.addWidget(arrangement_label)
        filter_row.addWidget(self.arrangement_filter)
        filter_row.addSpacing(8)
        filter_row.addWidget(self._make_separator())
        filter_row.addSpacing(8)
        filter_row.addWidget(date_label)
        filter_row.addWidget(date_from_label)
        filter_row.addWidget(self.date_from_filter)
        filter_row.addWidget(date_to_label)
        filter_row.addWidget(self.date_to_filter)
        filter_row.addStretch(1)
        filter_row.addWidget(sort_label)
        filter_row.addWidget(self.sort_combo)

        main_layout.addLayout(filter_row)

        # ── Row 3: Selection bar ─────────────────────────────────────────────
        selection_row = QHBoxLayout()

        self.selected_label = QLabel("0 jobs selected")
        fm = QFontMetrics(self.selected_label.font())
        width = fm.horizontalAdvance("9999 jobs selected")
        self.selected_label.setMinimumWidth(width)

        self.select_all_button = QPushButton(" Select all visible")
        self.select_all_button.setIcon(
            SelectIcon()
            )
        self.select_all_button.setObjectName("SelectionButton")
        self.select_all_button.clicked.connect(
            self.select_all_visible
            )
        self.select_all_button.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

        self.deselect_button = QPushButton(" Deselect")
        self.deselect_button.setIcon(
            DeselectIcon()
            )
        self.deselect_button.setObjectName("SelectionButton")
        self.deselect_button.clicked.connect(
            self.deselect_all
            )
        self.deselect_button.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

        self.delete_selected_button = QPushButton(" Delete")
        self.delete_selected_button.setIcon(
            TrashIcon(color_name="#DC6363")
            )
        self.delete_selected_button.setObjectName("SelectionButton")
        self.delete_selected_button.clicked.connect(
            self.delete_selected
            )
        self.delete_selected_button.setCursor(
            Qt.CursorShape.PointingHandCursor
            )

        selection_row.addWidget(self.selected_label)
        selection_row.addStretch()
        selection_row.addWidget(self.select_all_button)
        selection_row.addWidget(self.deselect_button)
        selection_row.addWidget(self.delete_selected_button)

        main_layout.addLayout(selection_row)

        # ── Body (scrollable) ────────────────────────────────────────────────
        body_container = QWidget()
        self.body_layout = QVBoxLayout(body_container)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(12)
        self.body_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setMinimumSize(410, 400)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(body_container)

        main_layout.addWidget(scroll, stretch=1)

    @staticmethod
    def _make_separator() -> QFrame:
        """Return a thin vertical separator line for the filter bar."""
        sep = QFrame()
        sep.setObjectName("filterSeparator")
        sep.setFixedSize(1, 30)
        return sep

    # TODO: Check that everything here actually make things better and fits all
    # distributions/OSs with dark and light themes
    def _apply_stylesheet(self) -> None:
        """Apply consolidated stylesheet for all components."""
        window_bg = self.palette().color(QPalette.ColorRole.Window)
        text_color = self.palette().color(QPalette.ColorRole.WindowText)
        base_bg = self.palette().color(QPalette.ColorRole.Base)
        button_bg = self.palette().color(QPalette.ColorRole.Button)
        highlight = self.palette().color(QPalette.ColorRole.Highlight)
        
        dialog_bg = window_bg.lighter(110)
        # Border color doesn't work in light themes
        border_color = window_bg.lighter(200)
        hover_bg = "rgba(128, 128, 128, 30)"
        overlay_bg = "rgba(0, 0, 0, 180)"
        alert_color = "#DC6363"
        hover_highlight = highlight.darker(90).name()
        
        stylesheet = f"""
            /* ==================== SEARCH BAR ==================== */
            QLineEdit#searchBar {{
                border: 1px solid {border_color.name()};
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
                }}
            QLineEdit#searchBar:hover {{
                background-color: {hover_bg};
                }}
            QLineEdit#searchBar:focus {{
                border: 1px solid palette(highlight);
                }}
            QPushButton#addApplicationButton {{
                background-color: palette(highlight);
                border: none;
                color: palette(highlighted-text);
                font-size: 14px;
                padding: 5px 6px;
                border-radius: 6px;
            }}
            QPushButton#addApplicationButton:hover {{
                background-color: {hover_highlight};
            }}
            
            /* ==================== FILTER BAR ==================== */
            QLabel#filterByLabel {{
                font-size: 14px;
                font-weight: 550;
                color: palette(window-text);
                }}
            QLabel#filterLabel {{
                font-size: 14px;
                color: palette(window-text);
                }}
            QComboBox#filterCombo {{
                border: 1px solid {border_color.name()};
                border-radius: 6px;
                padding: 0px 8px;
                font-size: 14px;
                }}
            QComboBox#filterCombo:hover {{
                background-color: {hover_bg};
                }}
            QComboBox#filterCombo::drop-down {{
                width: 0;
                }}
            QComboBox#filterCombo QAbstractItemView {{
                border: 1px solid palette(highlight);
                border-radius: 6px;
                selection-background-color: {hover_bg};
                }}
            QDateEdit#filterDate {{
                border: 1px solid {border_color.name()};
                font-size: 14px;
                }}
            QDateEdit#filterDate:hover {{
                background-color: {hover_bg};
                }}
            QFrame#filterSeparator {{
                background: {border_color.name()};
                }}

            /* ==================== SELECT BAR ==================== */
            QPushButton#SelectionButton {{
                border: none;
                font-size: 14px;
                padding: 8px 18px;
                border-radius: 6px;
            }}
            QPushButton#SelectionButton:hover {{
                background-color: {hover_bg};
            }}

            /* ==================== DELETE OVERLAY ==================== */

            QLabel#warningLabel {{
                color: {alert_color};
            }}

            /* ==================== JOB CARDS ==================== */
            QFrame#cardFrame {{
                border: 1px solid {border_color.name()};
                border-radius: 6px;
            }}
            QFrame#cardFrame:hover {{
                border: 1px solid {border_color.lighter(150).name()};
                background-color: {hover_bg};
            }}
            QFrame#cardFrame[selected="true"] {{
                border: 1px solid palette(highlight);
                border-radius: 6px;
            }}
            QFrame#cardFrame[selected="true"]:hover {{
                border: 1px solid palette(highlight);
                background-color: {hover_bg};
            }}
            QLabel#companyLabel {{
                font-weight: 600;
                font-size: 14px;
            }}
            QLabel#positionLabel {{
                font-size: 13px;
            }}
            QLabel#dateLabel, QLabel#locationLabel {{
                font-size: 11px;
                color: #666666;
            }}
            QPushButton#detailsButton {{
                background-color: transparent;
                border: none;
                font-size: 18px;
                padding: 4px 8px;
            }}
            QPushButton#detailsButton:hover {{
                background-color: {hover_bg};
                border-radius: 6px;
            }}
            
            /* ==================== OVERLAY BACKGROUNDS ==================== */
            QWidget#Overlay {{
                background-color: {overlay_bg};
                }}
            
            /* ==================== DIALOG FRAMES ==================== */
            QFrame#dialogFrame {{
                background-color: {dialog_bg.name()};
                border-radius: 12px;
                border: 1px solid {border_color.name()};
            }}
            
            /* ==================== DIALOG TITLES ==================== */
            QLabel#dialogTitle {{
                font-weight: 600; 
                font-size: 18px; 
                color: palette(window-text);
                letter-spacing: -0.3px;
            }}
            
            /* ==================== FORM INPUTS ==================== */
            QLineEdit#formInput, QTextEdit#formTextEdit {{
                border: 1px solid {border_color.name()};
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
                color: palette(window-text);
            }}
            QLineEdit#formInput:hover, QTextEdit#formTextEdit:hover {{
                background-color: {hover_bg};
            }}
            QLineEdit#formInput:focus, QTextEdit#formTextEdit:focus {{
                border: 1px solid palette(highlight);
            }}
            QDateEdit#formDate {{
                border: 1px solid {border_color.name()};
                font-size: 14px;
                }}
            QDateEdit#formDate:hover {{
                background-color: {hover_bg};
                }}

            /* ==================== COMBOBOX ==================== */
            QComboBox#formCombo {{
                border: 1px solid {border_color.name()};
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
                }}
            QComboBox#formCombo:hover {{
                background-color: {hover_bg};
                }}
            QComboBox#formCombo::drop-down {{
                width: 0;
                }}
            QComboBox#formCombo QAbstractItemView {{
                border: 1px solid palette(highlight);
                border-radius: 6px;
                selection-background-color: {hover_bg};
                }}

            /* ==================== VALUE LABELS (READ-ONLY) ==================== */
            QLabel#valueLabel {{
                background-color: {base_bg.name()};
                color: palette(window-text);
                border: none;
                border-radius: 6px;
                padding: 6px;
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
            
            QPushButton#removeBtn {{
                background-color: rgba(220, 53, 69, 210);
                border: none;
                color: palette(highlighted-text);
                font-size: 14px;
                padding: 8px 18px;
                border-radius: 6px;
            }}
            QPushButton#removeBtn:hover {{
                background-color: rgba(220, 53, 69, 235);
            }}
            
            QPushButton#closeBtn {{
                background-color: transparent;
                border: none;
                font-size: 18px;
                padding: 4px 8px;
                color: {text_color.darker(150).name()};
            }}
            QPushButton#closeBtn:hover {{
                background-color: {hover_bg};
                border-radius: 6px;
                color: palette(window-text);
            }}
            
            QPushButton#editBtn {{
                background-color: transparent;
                border: none;
                font-size: 16px;
                padding: 4px 8px;
                color: {text_color.darker(150).name()};
            }}
            QPushButton#editBtn:hover {{
                background-color: {hover_bg};
                border-radius: 6px;
                color: palette(window-text);
            }}
            
            /* ==================== SCROLL AREAS ==================== */
            QScrollArea#dialogScroll {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {base_bg.name()};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {border_color.name()};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {hover_bg};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """
        
        self.setStyleSheet(stylesheet)

    def add_application(self) -> None:
        """Open the in-window overlay popup to add a new job application."""
        if self._overlay is not None:
            self._overlay.deleteLater()
            self._overlay = None
        
        def on_submit(payload: NewJobDict) -> None:
            self.db.add_job(payload)
            self.refresh_from_db()
        
        self._overlay = AddApplicationOverlay(self, on_submit=on_submit)
        self._overlay.show()
        self._overlay.raise_()

    def open_view_overlay_for_job(self, job: JobDict) -> None:
        """Open the in-window overlay popup to view a job application."""
        if self._overlay is not None:
            self._overlay.deleteLater()
            self._overlay = None

        def on_remove(job_id: int) -> None:
            self.db.remove_job(job_id)
            self.refresh_from_db()

        def on_edit(job_payload: JobDict) -> None:
            self.open_edit_overlay_for_job(job_payload)

        self._overlay = ViewApplicationOverlay(
            self,
            job=job,
            on_remove=on_remove,
            on_edit=on_edit,
            )
        self._overlay.show()
        self._overlay.raise_()

    def open_edit_overlay_for_job(self, job: JobDict) -> None:
        """Open the in-window overlay popup to edit a job application."""
        if self._overlay is not None:
            self._overlay.deleteLater()
            self._overlay = None

        def on_remove(job_id: int) -> None:
            self.db.remove_job(job_id)
            self.refresh_from_db()

        def on_save(job_id: int, changes: dict[Any]) -> None:
            self.db.edit_job(job_id, **changes)
            self.refresh_from_db()

        self._overlay = EditApplicationOverlay(
            self,
            job=job,
            on_save=on_save,
            on_remove=on_remove,
        )
        self._overlay.show()
        self._overlay.raise_()

    def refresh_from_db(self) -> None:
        """Refreshes data from database in the UI."""
        self.query_all_job_apps()
        self.rebuild_cards()

    def query_all_job_apps(self) -> None:
        """
        Fetch all job applications from the database 
        into self.job_applications.
        """
        self.job_applications = self.db.get_all_jobs()
        self.job_companies = [j["company"] for j in self.job_applications if j.get("company")]
        self.job_positions = [j["position"] for j in self.job_applications if j.get("position")]
        self.job_locations = [j["location"] for j in self.job_applications if j.get("location")]
        self.completer_hints = self.job_companies + self.job_positions + self.job_locations
        self.update_completer_hints(self.completer_hints)

    def rebuild_cards(self) -> None:
        """Rebuilds job application cards."""
        self.clear_cards()

        for job in self.job_applications:
            w = JobApplicationCard(
                job,
                on_view = self.open_view_overlay_for_job,
                on_select_changed=self.selection_changed,
                )
            self.job_card_widgets.append(w)
            self.body_layout.insertWidget(
                self.body_layout.count() - 1, w, alignment=Qt.AlignmentFlag.AlignTop
                )
        self._sort_cards()

    def update_selection_bar(self):
        count = len(self.selected_job_ids)

        self.selected_label.setText(
            f"{count} job{'s' if count != 1 else ''} selected"
            )

        self.deselect_button.setEnabled(count > 0)
        self.delete_selected_button.setEnabled(count > 0)

    def select_all_visible(self):
        for widget in self.job_card_widgets:
            if widget.isVisible():
                job_id = int(widget.job["id"])
                self.selected_job_ids.add(job_id)
                widget.set_selected(True)

        self.update_selection_bar()

    def deselect_all(self):
        self.selected_job_ids.clear()

        for widget in self.job_card_widgets:
            widget.set_selected(False)

        self.update_selection_bar()

    def selection_changed(self, job_id: int, selected: bool):
        if selected:
            self.selected_job_ids.add(job_id)
        else:
            self.selected_job_ids.discard(job_id)

        self.update_selection_bar()

    def delete_selected(self):

        jobs = [
            widget.job
            for widget in self.job_card_widgets
            if int(widget.job["id"]) in self.selected_job_ids
            ]

        if not jobs:
            return

        self._overlay = BulkDeleteOverlay(
            self,
            jobs,
            self.confirm_bulk_delete
            )

        self._overlay.show()
        self._overlay.raise_()
        
    def confirm_bulk_delete(self, jobs):
        for job in jobs:
            self.db.remove_job(int(job["id"]))

        self.selected_job_ids.clear()
        self.refresh_from_db()
        self.update_selection_bar()

    def clear_cards(self) -> None:
        """Removes job application cards."""
        for w in getattr(self, "job_card_widgets"):
            self.body_layout.removeWidget(w)
            w.setParent(None)
            w.deleteLater()
        self.job_card_widgets = []

    def _sort_cards(self) -> None:
        """Re-order card widgets in body_layout according to the sort combo.

        "Not Applied" jobs (no date_applied) are always treated as the newest
        entry so they sort to the top when descending and to the bottom when
        ascending.
        """
        option = self.sort_combo.currentText()
        descending = "\u2193" in option

        if "Date applied" in option:
            sentinel_no_date = self._SORT_SENTINEL_NOT_APPLIED if descending else 0

            def sort_key(w: JobApplicationCard) -> int:
                if not w.job["date_applied"]:
                    return sentinel_no_date
                d = QDate.fromString(w.job["date_applied"], Qt.DateFormat.ISODate)
                return d.toJulianDay() if d.isValid() else sentinel_no_date
        else:
            def sort_key(w: JobApplicationCard) -> str:
                return w.job["last_update"] or ""

        sorted_widgets = sorted(self.job_card_widgets, key=sort_key, reverse=descending)

        for i, w in enumerate(sorted_widgets):
            self.body_layout.insertWidget(i, w, alignment=Qt.AlignmentFlag.AlignTop)

        self.update_jobs_displayed(self.searchbar.text())

    def update_jobs_displayed(self, text: str) -> None:
        t = (text or "").lower().strip()
        selected_status = (self.status_filter.currentText() or "").strip()
        selected_job_type = (self.job_type_filter.currentText() or "").strip()
        selected_arrangement = (self.arrangement_filter.currentText() or "").strip()

        date_from = self.date_from_filter.date()
        date_to = self.date_to_filter.date()
        no_lower_bound = (date_from == QDate(2000, 1, 1))

        for widget in self.job_card_widgets:
            # ── text search ──────────────────────────────────────────────
            matches_text = (
                (not t)
                or (t in widget.job["company"].lower())
                or (t in widget.job["position"].lower())
                or (t in (widget.job["location"] or "").lower())
            )

            # ── status filter ────────────────────────────────────────────
            matches_status = (
                selected_status == "Any"
                or widget.job["status"].strip() == selected_status
            )

            # ── job type filter ──────────────────────────────────────────
            matches_job_type = (
                selected_job_type == "Any"
                or widget.job["job_type"].strip() == selected_job_type
            )

            # ── work arrangement filter ──────────────────────────────────
            matches_arrangement = (
                selected_arrangement == "Any"
                or widget.job["work_arrangement"].strip() == selected_arrangement
            )

            # ── date range filter ────────────────────────────────────────
            # "Not Applied" jobs have no date — always show them regardless of
            # the date filter (unless they are excluded by another filter).
            matches_date = True
            if widget.job["date_applied"]:
                card_date = QDate.fromString(widget.job["date_applied"], Qt.DateFormat.ISODate)
                if card_date.isValid():
                    if not no_lower_bound and card_date < date_from:
                        matches_date = False
                    if card_date > date_to:
                        matches_date = False

            if (matches_text and matches_status and matches_job_type
                    and matches_arrangement and matches_date):
                widget.show()
            else:
                widget.hide()

    def update_completer_hints(self, hints: list[str]) -> None:
        self.completer.setModel(QStringListModel(hints))

    def resizeEvent(self, event: QShowEvent) -> None:
        """Handle window resize - update overlay if it's open."""
        super().resizeEvent(event)
        
        if self._overlay is not None and self._overlay.isVisible():
            self._overlay.setGeometry(self.rect())

    def add_job_from_extension(self, job: dict) -> None:
        """
        Handles a job application received from the browser extension via
        the local API server. Connected to bridge.job_received, so this
        runs on the GUI thread — safe to touch self.db and the UI directly.
        """
        normalised = {
            **job,
            **EXTENSION_ONLY_DEFAULTS,
            }
        print(normalised)
        self.db.add_job(normalised)
        self.refresh_from_db()