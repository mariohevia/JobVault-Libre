from pathlib import Path
from typing import Dict

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
)

from PyQt6.QtGui import QIcon, QPalette
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QStringListModel

from myapp.database import JobDatabase
from myapp.utils import (
    load_section_names_from_yaml, 
    load_cv_config,
    NoScrollDateEdit, 
    NoScrollComboBox,
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
        
        # Add section pages
        for section_def in self.section_defs:
            section_name = section_def.get("name", "")
            section_label = section_def.get("label", section_name)
            self._create_section_page(section_name, section_label)
        
        # Add Reorder Sections page
        self._create_section_page("reorder_sections", "Reorder Sections")
        
        # Add Preview page
        self._create_section_page("preview", "Preview CV")
        
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
        
    def _create_section_page(self, section_name: str, section_label: str) -> None:
        """Create and add a section page to the stack"""
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