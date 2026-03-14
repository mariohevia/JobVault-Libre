from typing import Callable

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
    )
from PyQt6.QtGui import QPalette, QShowEvent

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
    )
from myapp.constants import (
    STATUS_OPTIONS, 
    STATUS_COLORS, 
    JOB_TYPE_OPTIONS, 
    WORK_ARRANGEMENT_OPTIONS,
    )

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
        id: str,
        company: str,
        company_website: str | None,
        position: str,
        status: str,
        location: str | None,
        source: str | None,
        job_type: str | None,
        date_applied: str | None,
        contact_name: str | None,
        contact_email: str | None,
        salary_range: str | None,
        work_arrangement: str | None, 
        office_days: int,
        job_url: str | None,
        job_description: str | None,
        notes: str | None,
        cv_text: str | None,
        cover_letter_text: str | None,
        last_update: str | None,
        on_view: Callable | None = None,
        ) -> None:
        super().__init__()
        self.on_view = on_view
        self.id = id
        self.company = company
        self.company_website = company_website or ""
        self.position = position
        self.status = status
        self.location = location or ""
        self.source = source or ""
        self.job_type = job_type or ""
        self.date_applied = date_applied or ""
        self.contact_name = contact_name or ""
        self.contact_email = contact_email or ""
        self.salary_range = salary_range or ""
        self.work_arrangement = work_arrangement or ""
        self.office_days = office_days
        self.job_url = job_url or ""
        self.job_description = job_description or ""
        self.notes = notes or ""
        self.cv_text = cv_text or ""
        self.cover_letter_text = cover_letter_text or ""
        self.last_update = last_update or ""

        self.setMinimumWidth(400)
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
            )

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

        self.company_label = QLabel(self.company)
        self.company_label.setObjectName("companyLabel")
        self.company_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.status_badge = QLabel(self.status)
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setContentsMargins(8, 2, 8, 2)
        status_badge_color = STATUS_COLORS.get(self.status, "#6B7280")
        
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
        self.position_label = QLabel(self.position)
        self.position_label.setObjectName("positionLabel")

        if self.date_applied:
            date = QDate.fromString(self.date_applied, Qt.DateFormat.ISODate)
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

        self.location_label = QLabel(self.location)
        self.location_label.setObjectName("locationLabel")

        bottom_row.addWidget(self.location_label)
        bottom_row.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.details_button = QPushButton("More details")
        self.details_button.setObjectName("detailsButton")
        self.details_button.clicked.connect(self._handle_view_clicked) 
        bottom_row.addWidget(self.details_button)

        layout.addLayout(bottom_row)

    def _handle_view_clicked(self) -> None:
        if callable(self.on_view):
            self.on_view({
                "id": self.id,
                "company": self.company,
                "company_website": self.company_website,
                "position": self.position,
                "status": self.status,
                "location": self.location,
                "source": self.source,
                "job_type": self.job_type,
                "date_applied": self.date_applied,
                "contact_name": self.contact_name,
                "contact_email": self.contact_email,
                "salary_range": self.salary_range,
                "work_arrangement": self.work_arrangement,
                "office_days": self.office_days,
                "job_url": self.job_url,
                "job_description": self.job_description,
                "notes": self.notes,
                "cv_text": self.cv_text,
                "cover_letter_text": self.cover_letter_text,
                "last_update": self.last_update,
                })


class AddApplicationOverlay(QWidget):
    """
    An in-window overlay (covers parent) to add a job application
    The overlay closes when:
    - pressing the X button
    - pressing the Cancel button
    - clicking outside the popup panel
    - pressing Escape
    """
    def __init__(self, parent: QWidget, on_submit: Callable) -> None:
        super().__init__(parent)
        self.on_submit = on_submit

        self._build_ui()

        # Input validation styles
        self._base_style = ""
        self._error_style = "border: 2px solid #dc3545 !important;"

        # Capture outside clicks
        self.installEventFilter(self)

    def _build_ui(self) -> None:
        """Initializes the layout, creates widgets, and assembles the UI"""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setObjectName("addOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # ── Outer frame and layouts ──────────────────────────────────────────
        self.dialog = QFrame(self)
        self.dialog.setObjectName("dialogFrame")
        self.dialog.setMinimumSize(200,500)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(60, 40, 60, 80)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dialog_layout = QVBoxLayout(self.dialog)
        dialog_layout.setContentsMargins(24, 20, 24, 24)
        dialog_layout.setSpacing(16)

        # ── Title row (NOT scrollable) ───────────────────────────────────────
        title_row = QHBoxLayout()
        title = QLabel("Add Application")
        title.setObjectName("dialogTitle")

        close_btn = QPushButton("")
        close_btn.setIcon(CloseIcon())
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(32, 32)
        
        title_row.addWidget(title)
        title_row.addStretch()
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

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

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
        self.status.currentTextChanged.connect(self._on_status_changed)

        self.job_type = NoScrollComboBox()
        self.job_type.setObjectName("formCombo")
        self.job_type.addItems(JOB_TYPE_OPTIONS)

        self.work_arrangement = NoScrollComboBox()
        self.work_arrangement.addItems(WORK_ARRANGEMENT_OPTIONS)
        self.work_arrangement.setObjectName("formCombo")
        self.work_arrangement.currentTextChanged.connect(
            self._on_work_arrangement_changed
            )

        self.office_days = NoScrollComboBox()
        self.office_days.addItems(
            ["N/A", "Not specified"]+[str(i) for i in range(1,5)]
            )
        self.office_days.setObjectName("formCombo")
        self.office_days.setEnabled(False)

        self.company_website = QLineEdit()
        self.company_website.setObjectName("formInput")
        self.company_website.setPlaceholderText("https://...")

        self.location = QLineEdit()
        self.location.setObjectName("formInput")
        self.location.setPlaceholderText("e.g., London, UK")

        self.source = QLineEdit()
        self.source.setObjectName("formInput")
        self.source.setPlaceholderText("e.g., LinkedIn")

        self.date_applied = NoScrollDateEdit()
        self.date_applied.setObjectName("formDate")

        self.contact_name = QLineEdit()
        self.contact_name.setObjectName("formInput")
        self.contact_name.setPlaceholderText("Recruiter name")

        self.contact_email = QLineEdit()
        self.contact_email.setObjectName("formInput")
        self.contact_email.setPlaceholderText("email@company.com")

        self.salary_range = QLineEdit()
        self.salary_range.setObjectName("formInput")
        self.salary_range.setPlaceholderText("e.g., £100k - £150k")

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

        label_alignment = (
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
        label_alignment_single = (
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
            )

        def add_pair(
            row: int, 
            left_label: QLabel, 
            left_widget: QWidget, 
            right_label: QLabel, 
            right_widget: QWidget
            ) -> None:
            form.addWidget(left_label, row, 0, alignment=label_alignment)
            form.addWidget(left_widget, row, 1)
            form.addWidget(right_label, row, 2, alignment=label_alignment)
            form.addWidget(right_widget, row, 3)

        def add_single(
            row: int, 
            label: QLabel, 
            widget: QWidget, 
            alignment: Qt.AlignmentFlag | None = None
            ) -> None:
            if alignment:
                form.addWidget(label, row, 0, alignment=alignment)
            else:
                form.addWidget(label, row, 0, alignment=label_alignment)
            form.addWidget(widget, row, 1, 1, 3)

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
            l_text, l_required = l_meta
            r_text, r_required = r_meta
            add_pair(
                row,
                self._create_label(l_text, required=l_required), l_widget,
                self._create_label(r_text, required=r_required), r_widget,
                )
        singles = [
            ("Job URL", self.job_url, None),
            ("Company website", self.company_website, None),
            ("Job description", self.job_description, label_alignment_single),
            ("Notes", self.notes, label_alignment_single),
            ]

        start_row = len(pairs)

        for offset, (text, widget, alignment) in enumerate(singles):
            add_single(start_row + offset, QLabel(text), widget, alignment)

        scroll_layout.addLayout(form)
        scroll_area.setWidget(scroll_content)
        
        dialog_layout.addWidget(scroll_area, 1)  
        
        # ── Action buttons (NOT scrollable) ──────────────────────────────────
        actions = QHBoxLayout()
        actions.addStretch()

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
        dialog_layout.addLayout(actions)

        root_layout.addWidget(self.dialog)

    def _create_label(self, text: str, required: bool = False) -> QLabel:
        """Create a form label with optional required indicator."""
        label_text = f"{text} *" if required else text
        label = QLabel(label_text)
        return label

    def _on_status_changed(self, text: str) -> None:
        """Disable and clear date_applied when status is 'Not Applied'."""
        is_not_applied = (text == "Not Applied")
        if is_not_applied:
            self.date_applied.setSpecialValueText(" ")
            self.date_applied.setDate(self.date_applied.minimumDate())
            self.date_applied.setEnabled(False)
        else:
            self.date_applied.setSpecialValueText("")
            if self.date_applied.date() == self.date_applied.minimumDate():
                self.date_applied.setDate(QDate.currentDate())
            self.date_applied.setEnabled(True)

    def _on_work_arrangement_changed(self, text: str) -> None:
        """Disable office_days and set to 'N/A' when status is 'Hybrid'."""
        is_hybrid = (text == "Hybrid")
        self.office_days.setEnabled(is_hybrid)

        if is_hybrid:
            idx = self.office_days.findText("N/A")
            self.office_days.removeItem(idx)
            self.office_days.setCurrentIndex(0)
        else:
            if self.office_days.findText("N/A") == -1:
                self.office_days.addItem("N/A")
            idx = self.office_days.findText("N/A")
            self.office_days.setCurrentIndex(idx)

    def _submit(self) -> None:
        """Validate and submit the form."""
        company = self.company.text().strip()
        position = self.position.text().strip()
        status = self.status.currentText().strip()
        job_type = self.job_type.currentText().strip()
        work_arrangement = self.work_arrangement.currentText().strip()
        office_days = self.office_days.currentText().strip()
        if office_days=="N/A":
            office_days = None 
        elif office_days=="Not specified":
            office_days = 0
        else:
            office_days = int(office_days)

        is_valid = True
        
        if not company:
            self.company.setStyleSheet(self._error_style)
            is_valid = False
        else:
            self.company.setStyleSheet(self._base_style)
            
        if not position:
            self.position.setStyleSheet(self._error_style)
            is_valid = False
        else:
            self.position.setStyleSheet(self._base_style)

        if not is_valid:
            return

        if status == "Not Applied":
            date_applied_value = None
        else:
            date_applied_value = self.date_applied.date().toString(
                Qt.DateFormat.ISODate) or None

        payload = {
            "company": company,
            "position": position,
            "status": status,
            "work_arrangement": work_arrangement,
            "office_days": office_days,
            "company_website": self.company_website.text().strip() or None,
            "location": self.location.text().strip() or None,
            "source": self.source.text().strip() or None,
            "job_type": job_type,
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
        }

        self.on_submit(payload)
        self.close()
        
    def _fit_to_parent(self) -> None:
        """Resize overlay to match parent widget."""
        p = self.parentWidget()
        if p is not None:
            self.setGeometry(p.rect())

    def showEvent(self, event: QShowEvent) -> None:
        """Resize overlay to match parent widget when showed."""
        super().showEvent(event)
        self._fit_to_parent()
        self.position.setFocus()
        
    def resizeEvent(self, event: QShowEvent) -> None:
        """Handle window resize to keep overlay covering parent."""
        super().resizeEvent(event)
        self._fit_to_parent()

    def eventFilter(self, obj: QObject, event: QShowEvent) -> bool:
        """Close overlay when clicking outside the dialog."""
        if obj is self and event.type() == QEvent.Type.MouseButtonPress:
            if not self.dialog.geometry().contains(event.position().toPoint()):
                self.close()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QShowEvent) -> None:
        """Handle Escape key to close overlay."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

class ViewApplicationOverlay(QWidget):
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
        job: dict, 
        on_remove: Callable, 
        on_edit: Callable
        ) -> None:
        super().__init__(parent)
        self.job = dict(job)
        self.on_remove = on_remove
        self.on_edit = on_edit

        self._build_ui()

        # Capture outside clicks
        self.installEventFilter(self)

    def _build_ui(self) -> None:
        """Initializes the layout, creates widgets, and assembles the UI"""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setObjectName("viewOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # ── Outer frame and layouts ──────────────────────────────────────────
        self.dialog = QFrame(self)
        self.dialog.setObjectName("dialogFrame")
        self.dialog.setMinimumSize(200, 500)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(60, 40, 60, 80)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dialog_layout = QVBoxLayout(self.dialog)
        dialog_layout.setContentsMargins(24, 20, 24, 24)
        dialog_layout.setSpacing(16)

        # ── Title row (NOT scrollable) ───────────────────────────────────────
        title_row = QHBoxLayout()
        title = QLabel("Application Details")
        title.setObjectName("dialogTitle")

        edit_btn = QPushButton("")
        edit_btn.setIcon(EditIcon())
        edit_btn.setObjectName("editBtn")
        edit_btn.setToolTip("Edit application")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(self._open_edit_overlay)
        edit_btn.setFixedSize(32, 32)

        close_btn = QPushButton("")
        close_btn.setIcon(CloseIcon())
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(32, 32)

        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(edit_btn)
        title_row.addWidget(close_btn)

        dialog_layout.addLayout(title_row)

        # ── Read-only fields (scrollable) ────────────────────────────────────
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

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        label_alignment = (
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
        label_alignment_single = (
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
            )

        def make_value_label(key: str) -> QLabel:
            value = self.job.get(key, "")
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
            value_label.setTextInteractionFlags((
                Qt.TextInteractionFlag.TextSelectableByMouse
                | Qt.TextInteractionFlag.TextSelectableByKeyboard
                ))
            value_label.setWordWrap(True)
            return value_label

        def add_pair(
            row: int, 
            left_text: str, 
            left_key: str, 
            right_text: str, 
            right_key: str
            ) -> None:
            form.addWidget(
                QLabel(left_text), row, 0, alignment=label_alignment
                )
            form.addWidget(make_value_label(left_key), row, 1)
            form.addWidget(
                QLabel(right_text), row, 2, alignment=label_alignment
                )
            form.addWidget(make_value_label(right_key), row, 3)

        def add_single(
            row: int, 
            text: str, 
            key: str, 
            alignment: Qt.AlignmentFlag | None = None
            ) -> None:
            if alignment:
                form.addWidget(QLabel(text), row, 0, alignment=alignment)
            else:
                form.addWidget(QLabel(text), row, 0, alignment=label_alignment)
            form.addWidget(make_value_label(key), row, 1, 1, 3)

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
            add_pair(row, l_text, l_key, r_text, r_key)

        singles = [
            ("Job URL", "job_url", None),
            ("Company website", "company_website", None),
            ("Job description", "job_description", label_alignment_single),
            ("Notes", "notes", label_alignment_single),
            ("Last update", "last_update", None),
        ]

        start_row = len(pairs)

        for offset, (text, key, alignment) in enumerate(singles):
            add_single(start_row + offset, text, key, alignment)

        scroll_layout.addLayout(form)
        scroll_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        dialog_layout.addWidget(scroll_area, 1)

        # ── Action buttons (NOT scrollable) ──────────────────────────────────
        actions = QHBoxLayout()
        actions.addStretch()

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
        dialog_layout.addLayout(actions)

        root_layout.addWidget(self.dialog)

    def _open_edit_overlay(self) -> None:
        """Invokes the edit callback and closes the current dialog."""
        if callable(self.on_edit):
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

    def _fit_to_parent(self) -> None:
        """Resize overlay to match parent widget."""
        p = self.parentWidget()
        if p is not None:
            self.setGeometry(p.rect())

    def showEvent(self, event: QShowEvent) -> None:
        """Resize overlay to match parent widget when showed."""
        super().showEvent(event)
        self._fit_to_parent()

    def resizeEvent(self, event: QShowEvent) -> None:
        """Handle window resize to keep overlay covering parent."""
        super().resizeEvent(event)
        self._fit_to_parent()

    def eventFilter(self, obj: QObject, event: QShowEvent) -> bool:
        """Close overlay when clicking outside the dialog."""
        if obj is self and event.type() == QEvent.Type.MouseButtonPress:
            if not self.dialog.geometry().contains(event.position().toPoint()):
                self.close()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QShowEvent) -> None:
        """Handle Escape key to close overlay."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

class EditApplicationOverlay(QWidget):
    """
    An in-window overlay (covers parent) to edit a job application
    The overlay closes when:
    - pressing the X button
    - pressing the Cancel button
    - clicking outside the popup panel
    - pressing Escape
    """
    def __init__(
        self, 
        parent: QWidget, 
        job: dict, 
        on_save: Callable, 
        on_remove: Callable
        ) -> None:
        super().__init__(parent)
        self.job = dict(job)
        self.on_save = on_save
        self.on_remove = on_remove

        self._build_ui()

        # Input validation styles
        self._base_style = ""
        self._error_style = "border: 2px solid #dc3545 !important;"

        # Capture outside clicks
        self.installEventFilter(self)

    def _build_ui(self) -> None:
        """Initializes the layout, creates widgets, and assembles the UI"""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setObjectName("editOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # ── Outer frame and layouts ──────────────────────────────────────────
        self.dialog = QFrame(self)
        self.dialog.setObjectName("dialogFrame")
        self.dialog.setMinimumSize(200, 500)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(60, 40, 60, 80)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dialog_layout = QVBoxLayout(self.dialog)
        dialog_layout.setContentsMargins(24, 20, 24, 24)
        dialog_layout.setSpacing(16)

        # ── Title row (NOT scrollable) ───────────────────────────────────────
        title_row = QHBoxLayout()
        title = QLabel("Edit Application")
        title.setObjectName("dialogTitle")

        close_btn = QPushButton("")
        close_btn.setIcon(CloseIcon())
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(32, 32)

        title_row.addWidget(title)
        title_row.addStretch()
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

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self.company = QLineEdit(self.job.get("company") or "")
        self.company.setObjectName("formInput")
        self.company.setPlaceholderText("e.g., Google")

        self.position = QLineEdit(self.job.get("position") or "")
        self.position.setObjectName("formInput")
        self.position.setPlaceholderText("e.g., Software Engineer")

        self.status = NoScrollComboBox()
        self.status.setObjectName("formCombo")
        self.status.addItems(STATUS_OPTIONS)
        current_status = (self.job.get("status") or "").strip()
        idx = self.status.findText(current_status)
        self.status.setCurrentIndex(idx if idx >= 0 else 0)
        self.status.currentTextChanged.connect(self._on_status_changed)

        self.job_type = NoScrollComboBox()
        self.job_type.setObjectName("formCombo")
        self.job_type.addItems(JOB_TYPE_OPTIONS)
        current_job_type = (self.job.get("job_type") or "").strip()
        idx = self.job_type.findText(current_job_type)
        self.job_type.setCurrentIndex(idx if idx >= 0 else 0)

        self.work_arrangement = NoScrollComboBox()
        self.work_arrangement.addItems(WORK_ARRANGEMENT_OPTIONS)
        self.work_arrangement.setObjectName("formCombo")
        current_work_arrangement = (
            self.job.get("work_arrangement") or ""
            ).strip()
        idx = self.work_arrangement.findText(current_work_arrangement)
        self.work_arrangement.setCurrentIndex(idx if idx >= 0 else 0)
        self.work_arrangement.currentTextChanged.connect(
            self._on_work_arrangement_changed
            )
        
        self.office_days = NoScrollComboBox()
        self.office_days.setObjectName("formCombo")
        current_office_days = self.job.get("office_days")
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


        self.company_website = QLineEdit(self.job.get("company_website") or "")
        self.company_website.setObjectName("formInput")
        self.company_website.setPlaceholderText("https://...")

        self.location = QLineEdit(self.job.get("location") or "")
        self.location.setObjectName("formInput")
        self.location.setPlaceholderText("e.g., London, UK")

        self.source = QLineEdit(self.job.get("source") or "")
        self.source.setObjectName("formInput")
        self.source.setPlaceholderText("e.g., LinkedIn")

        existing_date_str = self.job.get("date_applied") or ""
        date = QDate.fromString(existing_date_str, Qt.DateFormat.ISODate)
        self.date_applied = NoScrollDateEdit(
            date=date if date.isValid() else None
            )
        self.date_applied.setObjectName("formDate")

        self.contact_name = QLineEdit(self.job.get("contact_name") or "")
        self.contact_name.setObjectName("formInput")
        self.contact_name.setPlaceholderText("Recruiter name")

        self.contact_email = QLineEdit(self.job.get("contact_email") or "")
        self.contact_email.setObjectName("formInput")
        self.contact_email.setPlaceholderText("email@company.com")

        self.salary_range = QLineEdit(self.job.get("salary_range") or "")
        self.salary_range.setObjectName("formInput")
        self.salary_range.setPlaceholderText("e.g., £100k - £150k")

        self.job_url = QLineEdit(self.job.get("job_url") or "")
        self.job_url.setObjectName("formInput")
        self.job_url.setPlaceholderText("https://...")

        self.job_description = BaseColourTextEdit()
        self.job_description.setObjectName("formTextEdit")
        self.job_description.setPlaceholderText(
            "Paste job description here..."
            )
        self.job_description.setAcceptRichText(True)
        self.job_description.setHtml(self.job.get("job_description") or "")
        self.job_description.setFixedHeight(150)
        
        self.notes = BaseColourTextEdit()
        self.notes.setObjectName("formTextEdit")
        self.notes.setPlaceholderText("Additional notes...")
        self.notes.setAcceptRichText(True)
        self.notes.setHtml(self.job.get("notes") or "")
        self.notes.setFixedHeight(150)

        label_alignment = (
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
        label_alignment_single = (
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
            )
        def add_pair(
            row: int, 
            left_label: QLabel, 
            left_widget: QWidget, 
            right_label: QLabel, 
            right_widget: QWidget
            ) -> None:
            form.addWidget(
                left_label, row, 0, alignment=label_alignment
                )
            form.addWidget(left_widget, row, 1)
            form.addWidget(
                right_label, row, 2, alignment=label_alignment
                )
            form.addWidget(right_widget, row, 3)

        def add_single(
            row: int, 
            label: QLabel, 
            widget: QWidget, 
            alignment: Qt.AlignmentFlag | None = None
            ) -> None:
            if alignment:
                form.addWidget(label, row, 0, alignment=alignment)
            else:
                form.addWidget(label, row, 0, alignment=label_alignment)
            form.addWidget(widget, row, 1, 1, 3)

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
            l_text, l_required = l_meta
            r_text, r_required = r_meta
            add_pair(
                row,
                self._create_label(l_text, required=l_required), l_widget,
                self._create_label(r_text, required=r_required), r_widget,
                )

        singles = [
            ("Job URL", self.job_url, None),
            ("Company website", self.company_website, None),
            ("Job description", self.job_description, label_alignment_single),
            ("Notes", self.notes, label_alignment_single),
            ]

        start_row = len(pairs)

        for offset, (text, widget, alignment) in enumerate(singles):
            add_single(start_row + offset, QLabel(text), widget, alignment)

        scroll_layout.addLayout(form)
        scroll_area.setWidget(scroll_content)

        dialog_layout.addWidget(scroll_area, 1)

        # ── Action buttons (NOT scrollable) ──────────────────────────────────
        actions = QHBoxLayout()
        actions.addStretch()

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
        dialog_layout.addLayout(actions)

        root_layout.addWidget(self.dialog)

    def _create_label(self, text: str, required: bool = False) -> QLabel:
        """Create a form label with optional required indicator."""
        label_text = f"{text} *" if required else text
        label = QLabel(label_text)
        return label

    def _on_status_changed(self, text: str) -> None:
        """Disable and clear date_applied when status is 'Not Applied'."""
        is_not_applied = (text == "Not Applied")
        if is_not_applied:
            self.date_applied.setSpecialValueText(" ")
            self.date_applied.setDate(self.date_applied.minimumDate())
            self.date_applied.setEnabled(False)
        else:
            self.date_applied.setSpecialValueText("")
            if self.date_applied.date() == self.date_applied.minimumDate():
                self.date_applied.setDate(QDate.currentDate())
            self.date_applied.setEnabled(True)

    def _on_work_arrangement_changed(self, text: str) -> None:
        """Disable office_days and set to 'N/A' when status is 'Hybrid'."""
        is_hybrid = (text == "Hybrid")
        self.office_days.setEnabled(is_hybrid)

        if is_hybrid:
            idx = self.office_days.findText("N/A")
            self.office_days.removeItem(idx)
            self.office_days.setCurrentIndex(0)
        else:
            if self.office_days.findText("N/A") == -1:
                self.office_days.addItem("N/A")
            idx = self.office_days.findText("N/A")
            self.office_days.setCurrentIndex(idx)

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
        job_id = self.job["id"]
        company = self.company.text().strip()
        position = self.position.text().strip()
        status = self.status.currentText().strip()
        job_type = self.job_type.currentText().strip()
        work_arrangement = self.work_arrangement.currentText().strip()
        office_days = self.office_days.currentText().strip()
        if office_days=="N/A":
            office_days = None 
        elif office_days=="Not specified":
            office_days = 0
        else:
            office_days = int(office_days)

        is_valid = True

        if not company:
            self.company.setStyleSheet(self._error_style)
            is_valid = False
        else:
            self.company.setStyleSheet(self._base_style)
            
        if not position:
            self.position.setStyleSheet(self._error_style)
            is_valid = False
        else:
            self.position.setStyleSheet(self._base_style)

        if not is_valid:
            return

        if status == "Not Applied":
            date_applied_value = None
        else:
            date_applied_value = self.date_applied.date().toString(Qt.DateFormat.ISODate) or None

        current = {
            "company": company,
            "position": position,
            "status": status,
            "work_arrangement": work_arrangement,
            "office_days": office_days,
            "company_website": self.company_website.text().strip() or None,
            "location": self.location.text().strip() or None,
            "source": self.source.text().strip() or None,
            "job_type": job_type,
            "date_applied": date_applied_value,
            "contact_name": self.contact_name.text().strip() or None,
            "contact_email": self.contact_email.text().strip() or None,
            "salary_range": self.salary_range.text().strip() or None,
            "job_url": self.job_url.text().strip() or None,
            "job_description": self.job_description.toHtml().strip() or None,
            "notes": self.notes.toHtml().strip() or None,
            # TODO: Handle cv and coverletter data
            # "cv_pdf": None,
            # "cv_text": None,
            # "cover_letter_pdf": None,
            # "cover_letter_text": None,
        }

        changes = {}
        for k, new_v in current.items():
            old_v = self.job.get(k)
            if new_v != old_v:
                changes[k] = new_v

        if changes:
            self.on_save(int(job_id), changes)

        self.close()

    def _fit_to_parent(self) -> None:
        """Resize overlay to match parent widget."""
        p = self.parentWidget()
        if p is not None:
            self.setGeometry(p.rect())

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._fit_to_parent()
        self.position.setFocus()

    def resizeEvent(self, event: QShowEvent) -> None:
        super().resizeEvent(event)
        self._fit_to_parent()

    def eventFilter(self, obj, event: QShowEvent) -> bool:
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

class TrackerPage(QWidget):

    ROWS_COMPLETER = 2
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
            ((self.searchbar.fontMetrics().height() + 4)
             * self.ROWS_COMPLETER + 2)
            )

        self.add_application_button = QPushButton("Add Application")
        self.add_application_button.clicked.connect(self.add_application)
        self.add_application_button.setCursor(
            Qt.CursorShape.PointingHandCursor
            )
        self.add_application_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
            )
        self.add_application_button.setMinimumHeight(34)

        search_row.addWidget(self.searchbar, stretch=1)
        search_row.addWidget(self.add_application_button)

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

        filter_row.addWidget(filter_icon_label)
        filter_row.addWidget(filter_by_label)
        filter_row.addWidget(status_label)
        filter_row.addWidget(self.status_filter)
        filter_row.addWidget(self._make_separator())
        filter_row.addWidget(job_type_label)
        filter_row.addWidget(self.job_type_filter)
        filter_row.addWidget(self._make_separator())
        filter_row.addWidget(arrangement_label)
        filter_row.addWidget(self.arrangement_filter)
        filter_row.addWidget(self._make_separator())
        filter_row.addWidget(date_label)
        filter_row.addWidget(date_from_label)
        filter_row.addWidget(self.date_from_filter)
        filter_row.addWidget(date_to_label)
        filter_row.addWidget(self.date_to_filter)
        filter_row.addStretch(1)
        filter_row.addWidget(self._make_separator())
        filter_row.addWidget(sort_label)
        filter_row.addWidget(self.sort_combo)

        main_layout.addLayout(filter_row)

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
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setObjectName("filterSeparator")
        sep.setFixedWidth(1)
        sep.setMinimumHeight(20)
        return sep

    # TODO: Check that everything here actually make things better and fits all
    # distributions/OSs
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
            /* ==================== SEARCH BAR ==================== */
            QLineEdit#searchBar {{
                border: 1px solid #cfcfcf;
                border-radius: 18px;
                padding: 6px;
                font-size: 12px;
            }}
            QLineEdit#searchBar:focus {{
                border: 1px solid #5a8dee;
            }}
            
            /* ==================== COMPLETER POPUP ==================== */
            QListView#completerPopup {{
                border: 1px solid #cccccc;
                border-radius: 2px;
                padding: 1px;
            }}
            QListView#completerPopup::item {{
                padding: 1px;
            }}
            QListView#completerPopup::item:selected {{
                border-radius: 2px;
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }}
            QListView#completerPopup::item:hover {{
                border-radius: 2px;
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }}
            
            /* ==================== FILTER BAR ==================== */
            QLabel#filterByLabel {{
                font-size: 12px;
                font-weight: 600;
                color: {text_color.name()};
            }}
            QLabel#filterLabel {{
                font-size: 11px;
                color: {text_color.darker(130).name()};
            }}
            QComboBox#filterCombo {{
                border: 1px solid {border_color.name()};
                border-radius: 4px;
                padding: 3px 6px;
                font-size: 11px;
                min-width: 80px;
            }}
            QComboBox#filterCombo:focus {{
                border: 1px solid {highlight.name()};
            }}
            QDateEdit#filterDate {{
                font-size: 11px;
            }}
            QFrame#filterSeparator {{
                color: {border_color.name()};
            }}

            /* ==================== JOB CARDS ==================== */
            QFrame#cardFrame {{
                border: 1px solid #cccccc;
                border-radius: 6px;
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
                font-size: 11px;
                padding: 4px 10px;
            }}
            
            /* ==================== OVERLAY BACKGROUNDS ==================== */
            QWidget#addOverlay, QWidget#viewOverlay, QWidget#editOverlay {{
                background-color: rgba(0, 0, 0, 180);
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
                color: {text_color.name()};
                letter-spacing: -0.3px;
            }}
            
            /* ==================== FORM INPUTS ==================== */
            QLineEdit#formInput, QTextEdit#formTextEdit {{
                background-color: {base_bg.name()};
                color: {text_color.name()};
                border: 1px solid {border_color.name()};
                border-radius: 6px;
                padding: 6px;
            }}
            QLineEdit#formInput:focus, QTextEdit#formTextEdit:focus {{
                border: 1px solid {highlight.name()};
            }}
            QDateEdit#formDate:disabled {{
                background-color: {button_bg.darker(105).name()};
                color: {text_color.darker(150).name()};
                border: 1px solid {border_color.darker(110).name()};
            }}
            
            /* ==================== COMBOBOX ==================== */
            QComboBox#formCombo {{
                border: 1px solid {border_color.name()};
                border-radius: 6px;
                padding: 6px;
            }}

            /* ==================== VALUE LABELS (READ-ONLY) ==================== */
            QLabel#valueLabel {{
                background-color: {base_bg.name()};
                color: {text_color.name()};
                border: none;
                border-radius: 6px;
                padding: 6px;
            }}
            
            /* ==================== VALUE TEXT EDIT (READ-ONLY) ==================== */
            QTextEdit#valueTextEdit {{
                background-color: {base_bg.name()};
                color: {text_color.name()};
                border: 1px solid {border_color.name()};
                border-radius: 6px;
                padding: 6px;
            }}
            
            /* ==================== BUTTONS ==================== */
            QPushButton#cancelBtn {{
                background-color: {button_bg.name()};
                color: {text_color.name()};
                border: 1px solid {border_color.name()};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton#cancelBtn:hover {{
                background-color: {hover_bg.name()};
            }}
            
            QPushButton#saveBtn {{
                background-color: {highlight.name()};
                border: 1px solid {highlight.name()};
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton#saveBtn:hover {{
                background-color: {highlight.darker(110).name()};
            }}
            
            QPushButton#removeBtn {{
                background-color: rgba(220, 53, 69, 210);
                border: 1px solid rgba(220, 53, 69, 210);
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
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
                background-color: rgba(128, 128, 128, 50);
                border-radius: 6px;
                color: {text_color.name()};
            }}
            
            QPushButton#editBtn {{
                background-color: transparent;
                border: none;
                font-size: 16px;
                padding: 4px 8px;
                color: {text_color.darker(150).name()};
            }}
            QPushButton#editBtn:hover {{
                background-color: rgba(128, 128, 128, 50);
                border-radius: 6px;
                color: {text_color.name()};
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
                background-color: {hover_bg.name()};
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
        
        def on_submit(payload: dict) -> None:
            self.db.add_job(**payload)
            self.refresh_from_db()
        
        self._overlay = AddApplicationOverlay(self, on_submit=on_submit)
        self._overlay.show()
        self._overlay.raise_()

    def open_view_overlay_for_job(self, job: dict) -> None:
        """Open the in-window overlay popup to view a job application."""
        if self._overlay is not None:
            self._overlay.deleteLater()
            self._overlay = None

        def on_remove(job_id: int) -> None:
            self.db.remove_job(job_id)
            self.refresh_from_db()

        def on_edit(job_payload: dict) -> None:
            self.open_edit_overlay_for_job(job_payload)

        self._overlay = ViewApplicationOverlay(
            self,
            job=job,
            on_remove=on_remove,
            on_edit=on_edit,
            )
        self._overlay.show()
        self._overlay.raise_()

    def open_edit_overlay_for_job(self, job: dict) -> None:
        """Open the in-window overlay popup to edit a job application."""
        if self._overlay is not None:
            self._overlay.deleteLater()
            self._overlay = None

        def on_remove(job_id: int) -> None:
            self.db.remove_job(job_id)
            self.refresh_from_db()

        def on_save(job_id: int, changes: dict) -> None:
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
                **job,
                on_view = self.open_view_overlay_for_job,
                )
            self.job_card_widgets.append(w)
            self.body_layout.insertWidget(
                self.body_layout.count() - 1, w, alignment=Qt.AlignmentFlag.AlignTop
                )
        self._sort_cards()

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
                if not w.date_applied:
                    return sentinel_no_date
                d = QDate.fromString(w.date_applied, Qt.DateFormat.ISODate)
                return d.toJulianDay() if d.isValid() else sentinel_no_date
        else:
            def sort_key(w: JobApplicationCard) -> str:
                return w.last_update or ""

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
                or (t in widget.company.lower())
                or (t in widget.position.lower())
                or (t in widget.location.lower())
            )

            # ── status filter ────────────────────────────────────────────
            matches_status = (
                selected_status == "Any"
                or widget.status.strip() == selected_status
            )

            # ── job type filter ──────────────────────────────────────────
            matches_job_type = (
                selected_job_type == "Any"
                or widget.job_type.strip() == selected_job_type
            )

            # ── work arrangement filter ──────────────────────────────────
            matches_arrangement = (
                selected_arrangement == "Any"
                or widget.work_arrangement.strip() == selected_arrangement
            )

            # ── date range filter ────────────────────────────────────────
            # "Not Applied" jobs have no date — always show them regardless of
            # the date filter (unless they are excluded by another filter).
            matches_date = True
            if widget.date_applied:
                card_date = QDate.fromString(widget.date_applied, Qt.DateFormat.ISODate)
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

    def resizeEvent(self, event):
        """Handle window resize - update overlay if it's open."""
        super().resizeEvent(event)
        
        if self._overlay is not None and self._overlay.isVisible():
            self._overlay.setGeometry(self.rect())