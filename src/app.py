import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QSizePolicy,
    QSpacerItem,
    QScrollArea,
    QLineEdit,
    QCompleter,
    QTextEdit,
    QComboBox,
    QFormLayout,
    QMessageBox,
    QStackedWidget,
)

from PyQt6.QtCore import Qt, QStringListModel, QEvent
from PyQt6.QtGui import QIcon, QPalette, QPixmap, QIcon

from database import JobDatabase
from tracker import TrackerPage
from utils import resource_path, get_app_paths_for_user

class MainWindow(QMainWindow):

    ROWS_COMPLETER = 2

    def __init__(self, user_paths):
        super().__init__()
        self.setWindowTitle("JobVault Libre")

        # Minimum size so the header always has room
        # self.setMinimumSize(820, 520)
        self.resize(1024,768)
        self.setMinimumWidth(450)

        # --- Database ---
        self.user_paths = user_paths
        self.db = JobDatabase(self.user_paths["db"])
        
        # --- Palette ---
        self.palette = QApplication.palette() 

        # --- Root container ---
        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

         # --- Left navigation panel ---
        nav = QFrame()
        nav.setFrameShape(QFrame.Shape.StyledPanel)
        nav.setFixedWidth(180)

        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(8, 8, 8, 8)
        nav_layout.setSpacing(8)

        logo_label = QLabel()   
        pixmap = QPixmap(resource_path("assets/JV_logo.png"))
        logo_label.setPixmap(
            pixmap.scaled(
                42, 42,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        logo_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title_label = QLabel(
            '<span style="font-size:14pt; font-weight:600; color: rgb(19, 64, 109);">'
            'JobVault </span> '
            '<span style="font-size:8pt; font-weight:500; color: rgb(120, 200, 80);">'
            'Libre</span>'
        )

        self.btn_applications = QPushButton("Applications")
        self.btn_applications.setCheckable(True)

        self.btn_other = QPushButton("Another page")
        self.btn_other.setCheckable(True)

        # horizontal layout just for logo + title
        nav_header_layout = QHBoxLayout()
        nav_header_layout.setContentsMargins(0, 0, 0, 0)
        nav_header_layout.setSpacing(8)

        nav_header_layout.addWidget(logo_label)
        nav_header_layout.addWidget(title_label)
        nav_header_layout.addStretch()  # pushes them to the left

        nav_layout.addLayout(nav_header_layout)
        nav_layout.addSpacing(12)
        nav_layout.addWidget(self.btn_applications)
        nav_layout.addWidget(self.btn_other)
        nav_layout.addStretch()

        root_layout.addWidget(nav)

         # --- Right side: stacked pages ---
        self.stack = QStackedWidget()
        root_layout.addWidget(self.stack, 1)

        self.applications_page = TrackerPage(self.db, self.palette, parent=self)
        self.stack.addWidget(self.applications_page)

        # TODO: Change this placeholder page
        self.other_page = QWidget()
        other_layout = QVBoxLayout(self.other_page)
        other_label = QLabel("New page content goes here")
        other_layout.addWidget(other_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(self.other_page)

        # --- Wire up navigation ---
        self.btn_applications.clicked.connect(
            lambda: self._switch_page(self.applications_page, self.btn_applications)
        )
        self.btn_other.clicked.connect(
            lambda: self._switch_page(self.other_page, self.btn_other)
        )

        # Start on applications page
        self._switch_page(self.applications_page, self.btn_applications)

    def _switch_page(self, page: QWidget, clicked_button: QPushButton):
        # Make sure only one nav button looks "active"
        for btn in (self.btn_applications, self.btn_other):
            btn.setChecked(btn is clicked_button)

        self.stack.setCurrentWidget(page)
        
    def closeEvent(self, event):
        try:
            self.db.close()
        finally:
            super().closeEvent(event)

def main():
    app = QApplication([])
    app.setWindowIcon(QIcon(resource_path("assets/JV_logo.png")))
    user_paths = get_app_paths_for_user("JobVaultLibre", user_id="Default")
    window = MainWindow(user_paths)
    window.show()
    app.exec()

if __name__ == "__main__":
    main()