import traceback
import sys
from importlib import resources

from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QDialog,
    QTextEdit,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QStackedWidget,
)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QGuiApplication, QFont

from myapp.database import JobDatabase
from myapp.tracker import TrackerPage
from myapp.cv_config import ProfilePage
from myapp.utils import get_app_paths_for_user
from myapp.exceptions import AppError

class FatalErrorDialog(QDialog):
    """
    Modal, application-blocking dialog that presents a fatal error/traceback.
    Provides Copy and Quit.
    """
    DEFAULT_TROUBLESHOOTING = [
        "Restart the application",
        "Update to the latest version if available",
        "Check if your disk has sufficient space"
    ]

    def __init__(
        self, 
        error_text: str, 
        exception: Exception | None = None,
        parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._error_text = error_text

        troubleshooting_steps = None
        if isinstance(exception, AppError) and exception.troubleshooting_steps:
            troubleshooting_steps = exception.troubleshooting_steps
        else:
            troubleshooting_steps = self.DEFAULT_TROUBLESHOOTING

        self.setWindowTitle("Fatal error")
        self.setModal(True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Keep it on top and remove the help button.
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        layout = QVBoxLayout(self)

        title = QLabel("The application encountered a fatal error and cannot continue.")
        title.setWordWrap(True)
        title_font = QFont()
        title_font.setPointSize(title_font.pointSize() + 2)
        title_font.setBold(True)
        title.setFont(title_font)

        # Troubleshooting section
        troubleshoot_label = QLabel("<b>Before reporting, please try:</b>")
        troubleshoot_label.setWordWrap(True)
        
        troubleshoot_steps = QLabel(
            "<br>".join(f"• {step}" for step in troubleshooting_steps)
        )
        troubleshoot_steps.setWordWrap(True)
        troubleshoot_steps.setTextFormat(Qt.TextFormat.RichText)
        troubleshoot_steps.setContentsMargins(10, 5, 10, 5)

        hint = QLabel("If the problem persists, copy the error details below and report it.")
        hint.setWordWrap(True)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlainText(self._error_text)
        self.text.setMinimumSize(760, 420)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        self.copy_btn = QPushButton("Copy Error Details")
        self.quit_btn = QPushButton("Quit")

        self.copy_btn.clicked.connect(self._copy)
        self.quit_btn.clicked.connect(self.accept)

        btn_row.addWidget(self.copy_btn)
        btn_row.addWidget(self.quit_btn)

        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(troubleshoot_label)
        layout.addWidget(troubleshoot_steps)
        layout.addSpacing(10)
        layout.addWidget(hint)
        layout.addSpacing(10)
        layout.addWidget(self.text)
        layout.addLayout(btn_row)
        self.copy_btn.setDefault(True)
        self.copy_btn.setFocus()

    def _copy(self) -> None:
        cb = QGuiApplication.clipboard()
        if cb is not None:
            cb.setText(self._error_text)

_fatal_shown = False
def install_exception_hook() -> None:
    def excepthook(exc_type, exc, tb):
        global _fatal_shown
        if _fatal_shown:
            return
        _fatal_shown = True

        app = QApplication.instance() or QApplication([])
        err_text = "".join(traceback.format_exception(exc_type, exc, tb))
        
        print(err_text, file=sys.stderr)
        parent = app.activeWindow()
        _fatal_dialog = FatalErrorDialog(err_text, exception=exc, parent=parent)
        _fatal_dialog.exec()
        app.quit()

    sys.excepthook = excepthook

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
        self.btn_profile = self._make_nav_button("CV Configuration")

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

def run_app() -> None:
    app = QApplication([])
    with resources.as_file(resources.files("myapp.assets").joinpath("JV_logo.png")) as path:
        app.setWindowIcon(QIcon(str(path)))
    
    user_paths = get_app_paths_for_user("JobVaultLibre", user_id="Default")
    window = MainWindow(user_paths)
    window.showMaximized()
    install_exception_hook()
    app.exec()

def main() -> None:
    try:
        run_app()
    except Exception as e:
        err_text = "".join(traceback.format_exception(*sys.exc_info()))
        print(err_text, file=sys.stderr)
        dlg = FatalErrorDialog(err_text, exception=e)
        dlg.exec()

if __name__ == "__main__":
    main()