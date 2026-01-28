
from importlib import resources

from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QStackedWidget,
)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap

from myapp.database import JobDatabase
from myapp.tracker import TrackerPage
from myapp.profile import ProfilePage
from myapp.utils import get_app_paths_for_user

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
        nav_layout.setSpacing(0)

        logo_label = QLabel()
        with resources.as_file(resources.files("myapp.assets").joinpath("JV_logo.png")) as path:
            pixmap = QPixmap(str(path))
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

        self.btn_applications = self._make_nav_button("Applications")
        self.btn_profile = self._make_nav_button("Profile")

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
        nav_layout.addWidget(self.btn_profile)
        nav_layout.addStretch()

        root_layout.addWidget(nav)

         # --- Right side: stacked pages ---
        self.stack = QStackedWidget()
        root_layout.addWidget(self.stack, 1)

        self.applications_page = TrackerPage(self.db, self.palette, parent=self)
        self.stack.addWidget(self.applications_page)

        self.profile_page = ProfilePage(self.palette, paths=self.user_paths)
        self.stack.addWidget(self.profile_page)

        # --- Wire up navigation ---
        self.btn_applications.clicked.connect(
            lambda: self._switch_page(self.applications_page, self.btn_applications)
        )
        self.btn_profile.clicked.connect(
            lambda: self._switch_page(self.profile_page, self.btn_profile)
        )

        # Start on applications page
        self._switch_page(self.applications_page, self.btn_applications)

        # TODO: Ensure that the colours used here fit for every theme or use a
        # theme based colour for everything
        self.setStyleSheet("""
            /* Nav buttons only */
            QPushButton[nav="true"] {
                background: transparent;
                border: none;
                padding: 8px 10px 8px 12px;   /* space for indicator */
                text-align: left;
                font-size: 10.5pt;
                font-weight: 500;
                color: palette(windowText);
            }

            /* Subtle hover: use Highlight with transparency (not a solid fill colour) */
            QPushButton[nav="true"]:hover {
                background: rgba(127, 127, 127, 23);
            }

            /* Pressed: slightly stronger */
            QPushButton[nav="true"]:pressed {
                background: rgba(127, 127, 127, 28);
            }

            /* Disabled */
            QPushButton[nav="true"]:disabled {
                color: rgba(127, 127, 127, 140);
                background: transparent;
            }

            /* Left indicator bar (implemented via padding + linear-gradient) */
            QPushButton[nav="true"]:checked {
                font-weight: 600;
                background:
                    qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 palette(highlight),
                                    stop:0.03 palette(highlight),
                                    stop:0.031 rgba(0,0,0,0),
                                    stop:1 rgba(127, 127, 127, 18));
            }

            /* Keep hover/press visible even when checked (optional refinement) */
            QPushButton[nav="true"]:checked:hover {
                background:
                    qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 palette(highlight),
                                    stop:0.04 palette(highlight),
                                    stop:0.041 rgba(0,0,0,0),
                                    stop:1 rgba(127,127,127,23));
            }
            QPushButton[nav="true"]:checked:pressed {
                background:
                    qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0 palette(highlight),
                                    stop:0.04 palette(highlight),
                                    stop:0.041 rgba(0,0,0,0),
                                    stop:1 rgba(127,127,127,28));
            }
            """)

    def _switch_page(self, page: QWidget, clicked_button: QPushButton):
        # Make sure only one nav button looks "active"
        for btn in (self.btn_applications, self.btn_profile):
            btn.setChecked(btn is clicked_button)

        self.stack.setCurrentWidget(page)
        
    def closeEvent(self, event):
        try:
            self.db.close()
        finally:
            super().closeEvent(event)

    @staticmethod
    def _make_nav_button(text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setProperty("nav", True)          # <-- used by QSS selector
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return btn

def main():
    app = QApplication([])
    with resources.as_file(resources.files("myapp.assets").joinpath("JV_logo.png")) as path:
        app.setWindowIcon(QIcon(str(path)))
    
    user_paths = get_app_paths_for_user("JobVaultLibre", user_id="Default")
    window = MainWindow(user_paths)
    window.showMaximized()
    app.exec()

if __name__ == "__main__":
    main()