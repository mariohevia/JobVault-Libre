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
)

from PyQt6.QtGui import QIcon, QPalette
from PyQt6.QtCore import Qt, pyqtSignal

from myapp.database import JobDatabase
from myapp.utils import load_section_names_from_yaml, load_cv_config


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
        back_btn = QPushButton("← Back")
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
        nav_row.setSpacing(4)
        
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
        
        nav_row.addStretch()
        
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
                padding: 4px 12px;
                font-size: 13px;
                border-radius: 4px;
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
        self.section_pages: Dict[str, SectionPlaceholderPage] = {}
        
        # Add Target Application page
        self._create_section_page("target_application", "Target Application")
        
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

    def show_subpage(self, index: int):
        if 0 <= index < self.subpages.count():
            self.subpages.setCurrentIndex(index)
    
    def _show_main_list(self) -> None:
        """Show the main CV list page"""
        self.subpages.setCurrentWidget(self.main_page)
    
    def _show_cv_editor(self) -> None:
        """Show the CV editor with navigation"""
        self.subpages.setCurrentWidget(self.editor_container)