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
)

from PyQt6.QtGui import QIcon, QPalette
from PyQt6.QtCore import Qt

from myapp.database import JobDatabase


class CVListPage(QWidget):

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

        add_button = QPushButton("Add CV")
        add_button.setFixedHeight(32)

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

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.subpages = QStackedWidget()
        self.layout.addWidget(self.subpages)

        self.main_page = CVListPage(db, palette, paths, self)
        self.page2 = QLabel("Subpage 2")

        self.subpages.addWidget(self.main_page)
        self.subpages.addWidget(self.page2)

    def show_subpage(self, index: int):
        if 0 <= index < self.subpages.count():
            self.subpages.setCurrentIndex(index)
