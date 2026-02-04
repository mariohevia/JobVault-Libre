from importlib import resources

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

from PyQt6.QtCore import Qt, QStringListModel, QEvent, QDate
from PyQt6.QtGui import QIcon, QPalette

from myapp.database import JobDatabase
from myapp.utils import NoScrollDateEdit, NoScrollComboBox, BaseColourTextEdit

# TODO: guarantee that the icon exists
SEARCH_ICON = QIcon.fromTheme("edit-find")
EDIT_ICON = QIcon.fromTheme("document-edit")
FILTER_ICON = QIcon.fromTheme("view-filter")
# search_icon = QIcon(":/icons/search.svg")  # or a local file

STATUS_OPTIONS = [
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
    "Remote"]

STATUS_COLORS = {
    "Applied": "#3B82F6",              # Blue - neutral/informative
    "Interview Scheduled": "#F59E0B",   # Amber - attention/upcoming
    "Interviewed": "#8B5CF6",           # Purple - in progress/waiting
    "Offer": "#2b7a2b",                 # Green - success/positive
    "Rejected": "#EF4444",              # Red - negative/closed
    "Withdrawn": "#6B7280",             # Gray - neutral/inactive
}

class JobApplicationCard(QWidget):
    def __init__(
        self,
        id,
        company,
        company_website,
        position,
        status,
        location,
        job_source,
        job_type,
        date_applied,
        contact_name,
        contact_email,
        salary_range,
        work_arrangement, 
        office_days,
        job_url,
        job_description,
        notes,
        last_update,
        on_view=None,
        **_ignored,
    ):
        super().__init__()
        self.on_view = on_view
        self.id = id
        self.company = company or ""
        self.company_website = company_website or ""
        self.position = position or ""
        self.status = status or ""
        self.location = location or ""
        self.job_source = job_source or ""
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
        self.last_update = last_update or ""

        self.setMinimumWidth(400)
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
            )

        self._init_ui()

    def _init_ui(self):

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
        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # --- Top row: Company + status badge ---
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

        # --- Middle row: Position + date applied ---
        self.position_label = QLabel(self.position)
        self.position_label.setObjectName("positionLabel")

        self.date_label = QLabel(f"Applied: {self.date_applied}")
        self.date_label.setObjectName("dateLabel")

        middle_row = QHBoxLayout()
        middle_row.setSpacing(8)
        middle_row.addWidget(self.position_label)
        middle_row.addStretch()
        middle_row.addWidget(self.date_label)

        # --- Bottom row: location + button bottom-right ---
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self.location_label = QLabel(self.location)
        self.location_label.setObjectName("locationLabel")

        bottom_row.addWidget(self.location_label)

        # spacer to push button to the right
        bottom_row.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.details_button = QPushButton("More details")
        self.details_button.setObjectName("detailsButton")
        self.details_button.clicked.connect(self._handle_view_clicked) 
        bottom_row.addWidget(self.details_button)

        # Add rows to main card layout
        layout.addLayout(top_row)
        layout.addLayout(middle_row)
        layout.addLayout(bottom_row)

    def _handle_view_clicked(self):
        if callable(self.on_view):
            # pass a job dict (same shape you already use elsewhere)
            self.on_view({
                "id": self.id,
                "company": self.company,
                "company_website": self.company_website,
                "position": self.position,
                "status": self.status,
                "location": self.location,
                "job_source": self.job_source,
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
                "last_update": self.last_update,
            })

class AddApplicationOverlay(QWidget):
    """
    An in-window overlay (covers parent) that closes when:
    - pressing the X button
    - clicking outside the popup panel
    """
    def __init__(self, parent: QWidget, on_submit):
        super().__init__(parent)
        self.on_submit = on_submit

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setObjectName("addOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(60, 40, 60, 80)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dialog = QFrame(self)
        self.dialog.setObjectName("dialogFrame")
        self.dialog.setMinimumSize(200,500)

        dialog_layout = QVBoxLayout(self.dialog)
        dialog_layout.setContentsMargins(24, 20, 24, 24)
        dialog_layout.setSpacing(16)

        # Title row + close button (NOT scrollable)
        title_row = QHBoxLayout()
        title = QLabel("Add Application")
        title.setObjectName("dialogTitle")
        title_row.addWidget(title)
        title_row.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(32, 32)
        title_row.addWidget(close_btn)

        dialog_layout.addLayout(title_row)

        # Scrollable area for the form
        scroll_area = QScrollArea()
        scroll_area.setObjectName("dialogScroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container for form content
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 8, 0)  # Small right margin for scrollbar
        scroll_layout.setSpacing(10)

        # Form
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
        self.job_type = NoScrollComboBox()
        self.job_type.setObjectName("formCombo")
        self.job_type.addItems(JOB_TYPE_OPTIONS)
        self.work_arrangement = NoScrollComboBox()
        self.work_arrangement.addItems(WORK_ARRANGEMENT_OPTIONS)
        self.work_arrangement.setObjectName("formCombo")
        self.work_arrangement.currentTextChanged.connect(self._on_work_arrangement_changed)
        self.office_days = NoScrollComboBox()
        self.office_days.addItems(["N/A", "Not specified"]+[str(i) for i in range(1,5)])
        self.office_days.setObjectName("formCombo")
        self.office_days.setEnabled(False)

        self.company_website = QLineEdit()
        self.company_website.setObjectName("formInput")
        self.company_website.setPlaceholderText("https://...")
        self.location = QLineEdit()
        self.location.setObjectName("formInput")
        self.location.setPlaceholderText("e.g., London, UK")
        self.job_source = QLineEdit()
        self.job_source.setObjectName("formInput")
        self.job_source.setPlaceholderText("e.g., LinkedIn")
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
        self.job_description.setPlaceholderText("Paste job description here...")
        self.job_description.setAcceptRichText(True)
        self.job_description.setFixedHeight(150)
        
        self.notes = BaseColourTextEdit()
        self.notes.setObjectName("formTextEdit")
        self.notes.setPlaceholderText("Additional notes...")
        self.notes.setAcceptRichText(True)
        self.notes.setFixedHeight(150)

        label_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        label_alignment_single = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop

        def add_pair(row, left_label, left_widget, right_label, right_widget):
            form.addWidget(left_label, row, 0, alignment=label_alignment)
            form.addWidget(left_widget, row, 1)
            form.addWidget(right_label, row, 2, alignment=label_alignment)
            form.addWidget(right_widget, row, 3)

        def add_single(row, label, widget, alignment=None):
            if alignment:
                form.addWidget(label, row, 0, alignment=alignment)
            else:
                form.addWidget(label, row, 0, alignment=label_alignment)
            form.addWidget(widget, row, 1, 1, 3)

        pairs = [
            (("Job title", True), self.position, ("Company", True), self.company),
            (("Date applied", False), self.date_applied, ("Status", True), self.status),
            (("Job location", False), self.location, ("Job type", False), self.job_type),
            (("Job source", False), self.job_source, ("Salary range", False), self.salary_range),
            (("Work arrangment", False), self.work_arrangement, ("Office days", False), self.office_days),
            (("Contact name", False), self.contact_name, ("Contact email", False), self.contact_email),
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
            add_single(
                start_row + offset,
                QLabel(text),
                widget,
                alignment
                )

        scroll_layout.addLayout(form)
        scroll_area.setWidget(scroll_content)
        
        dialog_layout.addWidget(scroll_area, 1)  # Stretch factor 1

        # Action buttons (NOT scrollable)
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

        outer.addWidget(self.dialog)

        # Capture outside clicks
        self.installEventFilter(self)

        # Store base styles for validation
        self._base_style = ""
        self._error_style = "border: 2px solid #dc3545 !important;"

    def _create_label(self, text: str, required: bool = False) -> QLabel:
        """Create a form label with optional required indicator."""
        label_text = f"{text} *" if required else text
        label = QLabel(label_text)
        return label

    def showEvent(self, event):
        super().showEvent(event)
        self._fit_to_parent()
        self.position.setFocus()

    def _on_work_arrangement_changed(self, text: str) -> None:
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

    def _fit_to_parent(self):
        """Resize overlay to match parent widget."""
        p = self.parentWidget()
        if p is not None:
            self.setGeometry(p.rect())

    def resizeEvent(self, event):
        """Handle window resize to keep overlay covering parent."""
        super().resizeEvent(event)
        self._fit_to_parent()

    def eventFilter(self, obj, event):
        """Close overlay when clicking outside the dialog."""
        if obj is self and event.type() == QEvent.Type.MouseButtonPress:
            if not self.dialog.geometry().contains(event.position().toPoint()):
                self.close()
                return True
        return super().eventFilter(obj, event)

    def _submit(self):
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

        # Validate required fields
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

        payload = {
            "company": company,
            "position": position,
            "status": status,
            "work_arrangement": work_arrangement,
            "office_days": office_days,
            "company_website": self.company_website.text().strip() or None,
            "location": self.location.text().strip() or None,
            "source": self.job_source.text().strip() or None,
            "job_type": job_type,
            "date_applied": self.date_applied.text().strip() or None,
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

    def keyPressEvent(self, event):
        """Handle Escape key to close overlay."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

# TODO: Sometimes text gets cut in half when the window is thin. Didn't fix this because I plan to change the view.
class ViewApplicationOverlay(QWidget):
    """
    In-window overlay (covers parent) that closes when:
    - pressing the X button
    - clicking outside the popup panel
    - pressing Escape

    Shows all values (read-only) and provides a Remove button.
    """
    def __init__(self, parent: QWidget, job: dict, on_remove, on_edit):
        super().__init__(parent)
        self.job = dict(job)  # defensive copy
        self.on_remove = on_remove
        self.on_edit = on_edit

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setObjectName("viewOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(60, 40, 60, 80)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dialog = QFrame(self)
        self.dialog.setObjectName("dialogFrame")
        self.dialog.setMinimumSize(200, 500)

        dialog_layout = QVBoxLayout(self.dialog)
        dialog_layout.setContentsMargins(32, 24, 32, 32)
        dialog_layout.setSpacing(20)

        # Title row + close button (NOT scrollable)
        title_row = QHBoxLayout()
        title = QLabel("Application Details")
        title.setObjectName("dialogTitle")
        title_row.addWidget(title)
        title_row.addStretch()

        edit_btn = QPushButton("")  # or "Edit"
        edit_btn.setIcon(EDIT_ICON)
        edit_btn.setObjectName("editBtn")
        edit_btn.setToolTip("Edit application")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setFixedSize(32, 32)
        edit_btn.clicked.connect(self._open_edit_overlay)
        title_row.addWidget(edit_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(32, 32)
        title_row.addWidget(close_btn)

        dialog_layout.addLayout(title_row)

        # Scrollable area for the read-only fields
        scroll_area = QScrollArea()
        scroll_area.setObjectName("dialogScroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 8, 0)
        scroll_layout.setSpacing(10)

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        label_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        label_alignment_single = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop

        def make_value_label(key: str) -> QLabel:
            value = self.job.get(key, "")
            if value == 0:
                value = "Not specified"
            if value is None or value == "":
                value = "—"
            value_label = QLabel(str(value))
            value_label.setObjectName("valueLabel")
            value_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            value_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
                | Qt.TextInteractionFlag.TextSelectableByKeyboard
            )
            value_label.setWordWrap(True)
            return value_label

        def add_pair(row, left_text, left_key, right_text, right_key):
            form.addWidget(QLabel(left_text), row, 0, alignment=label_alignment)
            form.addWidget(make_value_label(left_key), row, 1)
            form.addWidget(QLabel(right_text), row, 2, alignment=label_alignment)
            form.addWidget(make_value_label(right_key), row, 3)

        def add_single(row, text, key, alignment=None):
            if alignment:
                form.addWidget(QLabel(text), row, 0, alignment=alignment)
            else:
                form.addWidget(QLabel(text), row, 0, alignment=label_alignment)
            form.addWidget(make_value_label(key), row, 1, 1, 3)

        pairs = [
            ("Job title", "position", "Company", "company"),
            ("Date applied", "date_applied", "Status", "status"),
            ("Job location", "location", "Job type", "job_type"),
            ("Job source", "job_source", "Salary range", "salary_range"),
            ("Work arrangment", "work_arrangement", "Office days", "office_days"),
            ("Contact name", "contact_name", "Contact email", "contact_email"),
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
        remove.clicked.connect(self._remove_clicked)
        remove.setFixedHeight(36)

        actions.addWidget(close)
        actions.addSpacing(8)
        actions.addWidget(remove)
        dialog_layout.addLayout(actions)

        outer.addWidget(self.dialog)

        # Capture outside clicks
        self.installEventFilter(self)

    def showEvent(self, event):
        super().showEvent(event)
        self._fit_to_parent()

    def _open_edit_overlay(self):
        if callable(self.on_edit):
            self.on_edit(self.job)
        self.close()

    def _fit_to_parent(self):
        p = self.parentWidget()
        if p is not None:
            self.setGeometry(p.rect())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_to_parent()

    def eventFilter(self, obj, event):
        if obj is self and event.type() == QEvent.Type.MouseButtonPress:
            if not self.dialog.geometry().contains(event.position().toPoint()):
                self.close()
                return True
        return super().eventFilter(obj, event)

    def _remove_clicked(self):
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the application for {self.job.get('position', 'this position')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            job_id = self.job.get("id")
            if job_id is not None:
                self.on_remove(int(job_id))
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

class EditApplicationOverlay(QWidget):
    def __init__(self, parent: QWidget, job: dict, on_save, on_remove):
        super().__init__(parent)
        self.job = dict(job)          # original snapshot
        self.on_save = on_save        # fn(job_id:int, changes:dict)
        self.on_remove = on_remove    # fn(job_id:int)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setObjectName("editOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(60, 40, 60, 80)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dialog = QFrame(self)
        self.dialog.setObjectName("dialogFrame")
        self.dialog.setMinimumSize(200, 500)

        dialog_layout = QVBoxLayout(self.dialog)
        dialog_layout.setContentsMargins(24, 20, 24, 24)
        dialog_layout.setSpacing(16)

        # Title row
        title_row = QHBoxLayout()
        title = QLabel("Edit Application")
        title.setObjectName("dialogTitle")
        title_row.addWidget(title)
        title_row.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(32, 32)
        title_row.addWidget(close_btn)
        dialog_layout.addLayout(title_row)

        # Scrollable form
        scroll_area = QScrollArea()
        scroll_area.setObjectName("dialogScroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 8, 0)
        scroll_layout.setSpacing(10)

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        # Editable widgets
        self.company = QLineEdit(self.job.get("company") or "")
        self.company.setObjectName("formInput")
        self.company_website = QLineEdit(self.job.get("company_website") or "")
        self.company_website.setObjectName("formInput")
        self.position = QLineEdit(self.job.get("position") or "")
        self.position.setObjectName("formInput")

        self.status = NoScrollComboBox()
        self.status.setObjectName("formCombo")
        self.status.addItems(STATUS_OPTIONS)
        current_status = (self.job.get("status") or "").strip()
        idx = self.status.findText(current_status)
        self.status.setCurrentIndex(idx if idx >= 0 else 0)
        self.work_arrangement = NoScrollComboBox()
        self.work_arrangement.addItems(WORK_ARRANGEMENT_OPTIONS)
        self.work_arrangement.setObjectName("formCombo")
        current_work_arrangement = (self.job.get("work_arrangement") or "").strip()
        idx = self.work_arrangement.findText(current_work_arrangement)
        self.work_arrangement.setCurrentIndex(idx if idx >= 0 else 0)
        self.work_arrangement.currentTextChanged.connect(self._on_work_arrangement_changed)
        self.office_days = NoScrollComboBox()
        self.office_days.setObjectName("formCombo")
        current_office_days = self.job.get("office_days")
        if current_office_days is None:
            self.office_days.addItems(["N/A", "Not specified"]+[str(i) for i in range(1,5)])
            self.office_days.setEnabled(False)
        else:
            self.office_days.addItems(["Not specified"]+[str(i) for i in range(1,5)])
            self.office_days.setCurrentIndex(current_office_days)

        self.job_type = NoScrollComboBox()
        self.job_type.setObjectName("formCombo")
        self.job_type.addItems(JOB_TYPE_OPTIONS)
        current_job_type = (self.job.get("job_type") or "").strip()
        idx = self.job_type.findText(current_job_type)
        self.job_type.setCurrentIndex(idx if idx >= 0 else 0)

        self.location = QLineEdit(self.job.get("location") or "")
        self.location.setObjectName("formInput")
        self.job_source = QLineEdit(self.job.get("job_source") or "")
        self.job_source.setObjectName("formInput")
        date = QDate.fromString(self.job.get("date_applied"), Qt.DateFormat.ISODate)
        self.date_applied = NoScrollDateEdit(date)
        self.date_applied.setObjectName("formDate")
        self.contact_name = QLineEdit(self.job.get("contact_name") or "")
        self.contact_name.setObjectName("formInput")
        self.contact_email = QLineEdit(self.job.get("contact_email") or "")
        self.contact_email.setObjectName("formInput")
        self.salary_range = QLineEdit(self.job.get("salary_range") or "")
        self.salary_range.setObjectName("formInput")
        self.job_url = QLineEdit(self.job.get("job_url") or "")
        self.job_url.setObjectName("formInput")

        self.job_description = BaseColourTextEdit()
        self.job_description.setObjectName("formTextEdit")
        self.job_description.setAcceptRichText(True)
        self.job_description.setHtml(self.job.get("job_description") or "")
        self.job_description.setFixedHeight(150)
        
        self.notes = BaseColourTextEdit()
        self.notes.setObjectName("formTextEdit")
        self.notes.setAcceptRichText(True)
        self.notes.setHtml(self.job.get("notes") or "")
        self.notes.setFixedHeight(150)

        label_alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        label_alignment_single = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop

        def add_pair(row, left_text, left_widget, right_text, right_widget):
            form.addWidget(QLabel(left_text), row, 0, alignment=label_alignment)
            form.addWidget(left_widget, row, 1)
            form.addWidget(QLabel(right_text), row, 2, alignment=label_alignment)
            form.addWidget(right_widget, row, 3)

        def add_single(row, text, widget, alignment=None):
            if alignment:
                form.addWidget(QLabel(text), row, 0, alignment=alignment)
            else:
                form.addWidget(QLabel(text), row, 0, alignment=label_alignment)
            form.addWidget(widget, row, 1, 1, 3)

        pairs = [
            ("Job title", self.position, "Company", self.company),
            ("Date applied", self.date_applied, "Status", self.status),
            ("Job location", self.location, "Job type", self.job_type),
            ("Job source", self.job_source, "Salary range", self.salary_range),
            ("Work arrangment", self.work_arrangement, "Office days", self.office_days),
            ("Contact name", self.contact_name, "Contact email", self.contact_email),
            ]

        for row, (l_text, l_widget, r_text, r_widget) in enumerate(pairs):
            add_pair(row, l_text, l_widget, r_text, r_widget)

        singles = [
            ("Job URL", self.job_url, None),
            ("Company website", self.company_website, None),
            ("Job description", self.job_description, label_alignment_single),
            ("Notes", self.notes, label_alignment_single),
            ]

        start_row = len(pairs)

        for offset, (text, widget, alignment) in enumerate(singles):
            add_single(start_row + offset, text, widget, alignment)


        scroll_layout.addLayout(form)
        scroll_area.setWidget(scroll_content)
        dialog_layout.addWidget(scroll_area, 1)

        # Actions
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
        remove.clicked.connect(self._remove_clicked)
        remove.setFixedHeight(36)

        save = QPushButton("Save")
        save.setObjectName("saveBtn")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.clicked.connect(self._save_clicked)
        save.setFixedHeight(36)

        actions.addWidget(cancel)
        actions.addSpacing(8)
        actions.addWidget(remove)
        actions.addSpacing(8)
        actions.addWidget(save)
        dialog_layout.addLayout(actions)

        outer.addWidget(self.dialog)

        self.installEventFilter(self)

        # Store base styles for validation
        self._base_style = ""
        self._error_style = "border: 2px solid #dc3545 !important;"

    def showEvent(self, event):
        super().showEvent(event)
        self._fit_to_parent()
        self.position.setFocus()

    def _on_work_arrangement_changed(self, text: str) -> None:
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


    def _fit_to_parent(self):
        p = self.parentWidget()
        if p is not None:
            self.setGeometry(p.rect())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_to_parent()

    def eventFilter(self, obj, event):
        if obj is self and event.type() == QEvent.Type.MouseButtonPress:
            if not self.dialog.geometry().contains(event.position().toPoint()):
                self.close()
                return True
        return super().eventFilter(obj, event)

    def _remove_clicked(self):
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the application for {self.job.get('position', 'this position')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            job_id = self.job.get("id")
            if job_id is not None:
                self.on_remove(int(job_id))
            self.close()

    def _save_clicked(self):
        job_id = self.job.get("id")
        if job_id is None:
            return

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

        # Read current values
        current = {
            "company": company,
            "position": position,
            "status": status,
            "work_arrangement": work_arrangement,
            "office_days": office_days,
            "company_website": self.company_website.text().strip() or None,
            "location": self.location.text().strip() or None,
            "source": self.job_source.text().strip() or None,
            "job_type": job_type,
            "date_applied": self.date_applied.text().strip() or None,
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

        # Only send changed fields
        changes = {}
        for k, new_v in current.items():
            old_v = self.job.get(k)
            if new_v != old_v:
                changes[k] = new_v

        if changes:
            self.on_save(int(job_id), changes)

        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

class TrackerPage(QWidget):

    ROWS_COMPLETER = 2
    
    def __init__(self, db: JobDatabase, palette: QPalette, parent: QWidget | None = None):
        super().__init__(parent)
        self.db = db
        self.palette = palette

        root = self
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # --- Header ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)

        # --- Search bar ---
        # TODO: Figure out how to make the border round (StyleSheet is not working for that)
        # Maybe using a container widget could help
        self.searchbar = QLineEdit()
        self.searchbar.setObjectName("searchBar")
        self.searchbar.setPlaceholderText(
            "Search jobs by company, position, or location..."
            )
        self.searchbar.setClearButtonEnabled(True)
        self.searchbar.textChanged.connect(self.update_jobs_displayed)
        self.searchbar.addAction(
            SEARCH_ICON,
            QLineEdit.ActionPosition.LeadingPosition
            )

        # --- Status filter ---
        self.filter_label = QLabel()
        self.filter_label.setPixmap(FILTER_ICON.pixmap(16, 16))
        self.filter_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.status_filter = NoScrollComboBox()
        self.status_filter.setObjectName("formCombo")
        self.status_filter.addItem("All statuses")
        self.status_filter.addItems(STATUS_OPTIONS)
        self.status_filter.setMinimumHeight(34)
        self.status_filter.currentTextChanged.connect(
            lambda _text: self.update_jobs_displayed(self.searchbar.text()))

        # Adding Completer.
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.searchbar.setCompleter(self.completer)
        popup = self.completer.popup()
        popup.setObjectName("completerPopup")
        popup.setUniformItemSizes(True)
        popup.setMaximumHeight((self.searchbar.fontMetrics().height() + 4) * self.ROWS_COMPLETER + 2)

        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(8)

        search_row.addWidget(self.filter_label, stretch=0)
        search_row.addWidget(self.status_filter, stretch=0)
        search_row.addWidget(self.searchbar, stretch=1)

        title_layout.addLayout(search_row)
        header_layout.addLayout(title_layout, stretch=1)

        self.add_application_button = QPushButton("Add Application")
        self.add_application_button.clicked.connect(self.add_application)
        self.add_application_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_application_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.add_application_button.setMinimumHeight(34)

        header_layout.addWidget(self.add_application_button, alignment=Qt.AlignmentFlag.AlignTop)

        main_layout.addLayout(header_layout)

        # --- Scrollable body (only this part scrolls) ---
        body_container = QWidget()
        self.body_layout = QVBoxLayout(body_container)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(12)
        self.body_layout.addStretch(1)  # keeps cards pinned to the top

        scroll = QScrollArea()
        scroll.setMinimumSize(410, 400)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(body_container)

        main_layout.addWidget(scroll, stretch=1)

        self.job_applications = []
        self.job_card_widgets = []
        self._overlay = None

        # Apply consolidated stylesheet
        self._apply_stylesheet()

        self.refresh_from_db()

    def _apply_stylesheet(self):
        """Apply consolidated stylesheet for all components."""
        # Extract colors from palette
        window_bg = self.palette.color(QPalette.ColorRole.Window)
        text_color = self.palette.color(QPalette.ColorRole.WindowText)
        base_bg = self.palette.color(QPalette.ColorRole.Base)
        button_bg = self.palette.color(QPalette.ColorRole.Button)
        highlight = self.palette.color(QPalette.ColorRole.Highlight)
        
        # Create slightly lighter/darker variants
        dialog_bg = window_bg.lighter(110)
        border_color = window_bg.lighter(140)
        hover_bg = button_bg.lighter(120)
        
        # Get calendar icon path
        with resources.as_file(resources.files("myapp.resources.icons").joinpath("calendar.png")) as path:
            CALENDAR_ICON_PATH = str(path).replace("\\", "/")
        
        # Consolidated stylesheet
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
            QLineEdit#formInput, QTextEdit#formTextEdit, QDateEdit#formDate {{
                background-color: {base_bg.name()};
                color: {text_color.name()};
                border: 1px solid {border_color.name()};
                border-radius: 6px;
                padding: 6px;
            }}
            QLineEdit#formInput:focus, QTextEdit#formTextEdit:focus, QDateEdit#formDate:focus {{
                border: 1px solid {highlight.name()};
            }}
            
            /* ==================== DATE EDIT CALENDAR ICON ==================== */
            QDateEdit#formDate::down-arrow {{
                image: url("{CALENDAR_ICON_PATH}");
                width: 16px;
                height: 16px;
            }}
            QDateEdit#formDate::drop-down {{
                border: none;
                padding-right: 6px;
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

    def add_application(self):
        """Open the in-window overlay popup to add a new job application."""
        # Properly clean up existing overlay
        if self._overlay is not None:
            self._overlay.deleteLater()
            self._overlay = None
        
        def on_submit(payload: dict):
            self.db.add_job(**payload)
            self.refresh_from_db()
        
        self._overlay = AddApplicationOverlay(self, on_submit=on_submit)
        self._overlay.show()
        self._overlay.raise_()

    def open_view_overlay_for_job(self, job: dict):
        if self._overlay is not None:
            self._overlay.deleteLater()
            self._overlay = None

        def on_remove(job_id: int):
            self.db.remove_job(job_id)
            self.refresh_from_db()

        def on_edit(job_payload: dict):
            # close view overlay happens inside _open_edit_overlay
            self.open_edit_overlay_for_job(job_payload)

        self._overlay = ViewApplicationOverlay(
            self,
            job=job,
            on_remove=on_remove,
            on_edit=on_edit,
        )
        self._overlay.show()
        self._overlay.raise_()

    def open_edit_overlay_for_job(self, job: dict):
        if self._overlay is not None:
            self._overlay.deleteLater()
            self._overlay = None

        def on_remove(job_id: int):
            self.db.remove_job(job_id)
            self.refresh_from_db()

        def on_save(job_id: int, changes: dict):
            # changes contains only keys that actually changed
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

    def query_all_job_apps(self):
        """Fetch all job applications from the database into self.job_applications."""
        rows = self.db.get_all_jobs()

        # get_all_jobs returns:
        # (id, company, company_website, position, status, location,
        #  date_applied, contact_name, contact_email, salary_range,
        #  job_url, job_description, notes, cv_text, cover_letter_text, last_update)
        self.job_applications = []
        for r in rows:
            self.job_applications.append({
                "id": r[0],
                "company": r[1],
                "company_website": r[2],
                "position": r[3],
                "status": r[4],
                "location": r[5],
                "job_source": r[6],
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
                # TODO: PDFs and extracted text are intentionally ignored in the UI.
            })

        self.job_companies = [j["company"] for j in self.job_applications if j.get("company")]
        self.job_positions = [j["position"] for j in self.job_applications if j.get("position")]
        self.job_locations = [j["location"] for j in self.job_applications if j.get("location")]
        self.completer_hints = self.job_companies + self.job_positions + self.job_locations
        self.update_completer_hints(self.completer_hints)

    # ---------- UI refresh ----------
    def refresh_from_db(self):
        self.query_all_job_apps()
        self.rebuild_cards()

    def rebuild_cards(self):
        self.clear_cards()

        self.job_card_widgets = []
        for job in self.job_applications:
            w = JobApplicationCard(
                **job,
                on_view=self.open_view_overlay_for_job,  # <- MainWindow method
            )
            self.job_card_widgets.append(w)
            self.body_layout.insertWidget(
                self.body_layout.count() - 1, w, alignment=Qt.AlignmentFlag.AlignTop
            )
        self.update_jobs_displayed(self.searchbar.text())

    def clear_cards(self):
        # remove all widgets except the final stretch item
        for w in getattr(self, "job_card_widgets", []):
            self.body_layout.removeWidget(w)
            w.setParent(None)
            w.deleteLater()
        self.job_card_widgets = []

    def update_jobs_displayed(self, text):
        t = (text or "").lower().strip()
        selected_status = (self.status_filter.currentText() or "").strip()

        for widget in self.job_card_widgets:
            matches_text = (
                (not t)
                or (t in widget.company.lower())
                or (t in widget.position.lower())
                or (t in widget.location.lower())
            )

            matches_status = (
                selected_status == "All statuses"
                or widget.status.strip() == selected_status
            )

            if matches_text and matches_status:
                widget.show()
            else:
                widget.hide()

    def update_completer_hints(self, hints: list[str]):
        self.completer.setModel(QStringListModel(hints))

    def resizeEvent(self, event):
        """Handle window resize - update overlay if it's open."""
        super().resizeEvent(event)
        
        # Update overlay geometry when window is resized
        if self._overlay is not None and self._overlay.isVisible():
            self._overlay.setGeometry(self.rect())