import traceback
import sys
import threading

from myapp.api_server import bridge, run_server

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
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QGuiApplication, QFont

from myapp.database import JobDatabase
from myapp.tracker import TrackerPage
from myapp.cv_config import ProfilePage
from myapp.cv_builder import CVBuilderPage
from myapp.support_project import SupportPage
from myapp.settings import SettingsPage, load_settings
from myapp.utils import get_app_paths_for_user
from myapp.exceptions import AppError
from myapp.icons import LogoIcon, SettingsIcon

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

        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            )

        layout = QVBoxLayout(self)

        title = QLabel(
            "The application encountered a fatal error and cannot continue."
            )
        title.setWordWrap(True)
        title_font = QFont()
        title_font.setPointSize(title_font.pointSize() + 2)
        title_font.setBold(True)
        title.setFont(title_font)

        troubleshoot_label = QLabel("<b>Before reporting, please try:</b>")
        troubleshoot_label.setWordWrap(True)
        
        troubleshoot_steps = QLabel(
            "<br>".join(f"• {step}" for step in troubleshooting_steps)
        )
        troubleshoot_steps.setWordWrap(True)
        troubleshoot_steps.setTextFormat(Qt.TextFormat.RichText)
        troubleshoot_steps.setContentsMargins(10, 5, 10, 5)

        hint = QLabel(
            "If the problem persists, "
            "copy the error details below and report it."
            )
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
        assert cb is not None, (
            "Clipboard unavailable — "
            "no QGuiApplication instance"
            )
        cb.setText(self._error_text)

def install_exception_hook() -> None:
    original_hook = sys.excepthook
    fatal_shown = False
    def excepthook(exc_type, exc_val, tb):
        nonlocal fatal_shown
        if fatal_shown:
            return
        fatal_shown = True

        err_text = "".join(traceback.format_exception(exc_type, exc_val, tb))
        print(err_text, file=sys.stderr)

        app = QApplication.instance()   
        if app is None:
            original_hook(exc_type, exc_val, tb)
            return
        try:
            parent = app.activeWindow()
            _fatal_dialog = FatalErrorDialog(
                err_text, 
                exception=exc_val, 
                parent=parent
                )
            _fatal_dialog.exec()
        except Exception:
            original_hook(*sys.exc_info())
        finally:
            app.quit()

    sys.excepthook = excepthook

class MainWindow(QMainWindow):
    """
    Application shell. Owns the left navigation panel and the stacked page area.
    All top-level pages are created here and wired to their nav buttons.
    """

    def __init__(self, user_paths) -> None:
        super().__init__()
        self.user_paths = user_paths
        self.db = JobDatabase(self.user_paths["db"])
        self.palette = QApplication.palette() 
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("JobVault Libre")
        self.resize(1024,768)
        self.setMinimumWidth(450)

        # ── Root container ───────────────────────────────────────────────────
        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

         # ── Left navigation panel ───────────────────────────────────────────
        nav = QFrame()
        nav.setFrameShape(QFrame.Shape.StyledPanel)
        nav.setFixedWidth(180)

        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(8, 8, 8, 8)
        nav_layout.setSpacing(0)

        logo_label = QLabel()
        pixmap = LogoIcon().pixmap(42, 42)
        logo_label.setPixmap(
            pixmap.scaled(
                42, 42,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
                )
            )
        logo_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title_label = QLabel(
            '<span style="font-size:14pt; font-weight:600; '
            'color: rgb(19, 64, 159);">JobVault </span> '
            '<span style="font-size:8pt; font-weight:500; '
            'color: rgb(120, 200, 80);">Libre</span>'
            )

        self.btn_applications = self._make_nav_button("Applications")
        # self.btn_profile = self._make_nav_button("CV Configuration")
        # self.btn_builder = self._make_nav_button("CV Builder")
        self.btn_support_project = self._make_nav_button("Support Us")

        icon_settings_size = 32
        btn_settings_size = 40
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(
            SettingsIcon(size=icon_settings_size,color_name="#aaaaaa")
            )
        self.btn_settings.setObjectName("settingsBtn")
        self.btn_settings.setToolTip("Settings")
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setFixedSize(btn_settings_size, btn_settings_size)
        self.btn_settings.setIconSize(
            QSize(icon_settings_size, icon_settings_size)
            )

        nav_header_layout = QHBoxLayout()
        nav_header_layout.setContentsMargins(0, 0, 0, 0)
        nav_header_layout.setSpacing(8)

        nav_header_layout.addWidget(logo_label)
        nav_header_layout.addWidget(title_label)
        nav_header_layout.addStretch()

        nav_layout.addLayout(nav_header_layout)
        nav_layout.addSpacing(12)
        nav_layout.addWidget(self.btn_applications)
        # nav_layout.addWidget(self.btn_profile)
        # nav_layout.addWidget(self.btn_builder)
        nav_layout.addWidget(self.btn_support_project)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_settings, alignment=Qt.AlignmentFlag.AlignLeft)

        root_layout.addWidget(nav)

         # ── Right side: stacked pages ───────────────────────────────────────
        self.stack = QStackedWidget()
        root_layout.addWidget(self.stack, 1)

        self.applications_page = TrackerPage(self.db, parent=self)
        self.stack.addWidget(self.applications_page)

        self.profile_page = ProfilePage(self.palette, paths=self.user_paths)
        self.stack.addWidget(self.profile_page)

        self.builder_page = CVBuilderPage(self.db, paths=self.user_paths)
        self.stack.addWidget(self.builder_page)

        self.support_page = SupportPage(self.palette)
        self.stack.addWidget(self.support_page)

        self.settings_page = SettingsPage(self.user_paths["settings"])
        self.stack.addWidget(self.settings_page)

        # ── Wire up navigation ───────────────────────────────────────────────────
        self.btn_applications.clicked.connect(
            lambda: self._switch_page(self.applications_page, self.btn_applications)
            )
        # self.btn_profile.clicked.connect(
        #     lambda: self._switch_page(self.profile_page, self.btn_profile)
        # )
        # self.btn_builder.clicked.connect(
        #     lambda: self._switch_page(self.builder_page, self.btn_builder)
        # )
        self.btn_support_project.clicked.connect(
            lambda: self._switch_page(self.support_page, self.btn_support_project)
            )

        self.btn_settings.clicked.connect(
            lambda: self._switch_page(self.settings_page, self.btn_settings)
            )

        self._switch_page(self.applications_page, self.btn_applications)

        # TODO: Ensure that the colours used here fit for every theme or use a
        # theme based colour for everything
        self.setStyleSheet(self._get_stylesheet())
        

    def _get_stylesheet(self) -> str:
        return """
            QPushButton[nav="true"] {
                background: transparent;
                border: none;
                padding: 8px 10px 8px 12px;
                text-align: left;
                font-size: 10.5pt;
                font-weight: 500;
                color: palette(windowText);
            }
            QPushButton[nav="true"]:hover {
                background: palette(midlight);
            }
            QPushButton[nav="true"]:pressed {
                background: palette(mid);
            }
            QPushButton[nav="true"]:disabled {
                color: palette(placeholderText);
                background: transparent;
            }
            QPushButton[nav="true"]:checked {
                font-weight: 600;
                background:
                    qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0    palette(highlight),
                                    stop:0.03 palette(highlight),
                                    stop:0.031 transparent,
                                    stop:1    palette(window));
            }
            QPushButton[nav="true"]:checked:hover {
                background:
                    qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0    palette(highlight),
                                    stop:0.04 palette(highlight),
                                    stop:0.041 transparent,
                                    stop:1    palette(midlight));
            }
            QPushButton[nav="true"]:checked:pressed {
                background:
                    qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop:0    palette(highlight),
                                    stop:0.04 palette(highlight),
                                    stop:0.041 transparent,
                                    stop:1    palette(mid));
            }
            QPushButton#settingsBtn {
                background-color: transparent;
                border: none;
                padding: 0px;
                color: #aaaaaa;
            }
            QPushButton#settingsBtn:hover {
                background-color: rgba(128, 128, 128, 30);
                border-radius: 6px;
                color: palette(window-text);
            }
        """

    def _switch_page(self, page: QWidget, clicked_button: QPushButton) -> None:
        for btn in (
            self.btn_applications,
            # self.btn_profile,
            # self.btn_builder,
            self.btn_support_project
            ):
            btn.setChecked(btn is clicked_button)

        self.stack.setCurrentWidget(page)
        
    def closeEvent(self, event) -> None:
        try:
            self.db.close()
        finally:
            super().closeEvent(event)

    @staticmethod
    def _make_nav_button(text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setProperty("nav", True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return btn

def run_app() -> None:
    app = QApplication([])
    app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    app.setWindowIcon(LogoIcon())

    user_paths = get_app_paths_for_user("JobVaultLibre", user_id="Default")
    window = MainWindow(user_paths)

    # Refresh the tracker page whenever the extension posts a new job
    bridge.job_received.connect(window.applications_page.add_job_from_extension)

    settings = load_settings(user_paths["settings"])
    server_port = settings['JobVault Libre Extension']['jobvault_app_port']
    server_thread = threading.Thread(
        target=run_server, kwargs={"port": server_port}, daemon=True
        )
    server_thread.start()

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