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
    QListWidget, 
    QListWidgetItem, 
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
    "Remote"]

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


class JobApplicationCard(QWidget):
    # TODO: Implement these widgets
    def __init__(self, job_data: dict, parent: QWidget | None = None):
        super().__init__(parent)

        self._job_data = job_data  # store full job info

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Job title (position)
        title = self._job_data.get("position", "Untitled Position")

        self.title_label = QLabel(title)
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self.title_label)


class TargetApplicationPage(QWidget):
    """Placeholder page for each CV section"""
    
    ROWS_COMPLETER = 2

    def __init__(
        self, 
        db: JobDatabase, 
        palette: QPalette, 
        section_name: str, 
        section_label: str,
        parent: QWidget | None = None
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
        
        # ── Row 1: Search bar + Add button ─────────────────────────────────
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
            QLineEdit.ActionPosition.LeadingPosition
        )
        
        # Adding Completer
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

        # Filter icon + label
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

        # Status filter
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

        # Separator
        filter_row.addWidget(self._make_separator())

        # Job type filter
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

        # Separator
        filter_row.addWidget(self._make_separator())

        # Work arrangement filter
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

        # Separator
        filter_row.addWidget(self._make_separator())

        # Date applied range filter
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
        self.date_from_filter.setSpecialValueText(" ")   # blank when at minimum
        self.date_from_filter.setMinimumDate(QDate(2000, 1, 1))
        self.date_from_filter.setMaximumDate(today)
        self.date_from_filter.setDate(QDate(2000, 1, 1))  # default = no lower bound
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

        # Sort order
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

        filter_row.addWidget(sort_label)
        filter_row.addWidget(self.sort_combo)

        layout.addLayout(filter_row)

        # ── Job List ──────────────────────────────────────────────
        self.job_list = QListWidget()
        self.job_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.job_list.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self.job_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        layout.addWidget(self.job_list)

        self.query_all_job_apps()
        self.populate_job_list()

    
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

    def populate_job_list(self):
        self.job_list.clear()

        for job in self.job_applications:
            item = QListWidgetItem(self.job_list)

            # store full job data inside the item
            item.setData(Qt.ItemDataRole.UserRole, job)

            # create your custom card widget
            card = JobApplicationCard(job)

            # make row height match card
            item.setSizeHint(card.sizeHint())

            self.job_list.addItem(item)
            self.job_list.setItemWidget(item, card)

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

    def update_jobs_displayed(self, text):
        # TODO: Implement all things properly similar to tracker.py
        for i in range(self.job_list.count()):
            item = self.job_list.item(i)
            job = item.data(Qt.ItemDataRole.UserRole)

            matches = (
                text in (job.get("company") or "").lower()
                or text in (job.get("position") or "").lower()
                or text in (job.get("location") or "").lower()
            )

            item.setHidden(not matches)

    def get_selected_job(self):
        item = self.job_list.currentItem()
        if not item:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def update_completer_hints(self, hints: list[str]):
        self.completer.setModel(QStringListModel(hints))

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