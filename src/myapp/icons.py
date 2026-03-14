from importlib import resources

from PyQt6.QtGui import QIcon, QPixmap, QPalette, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QByteArray, Qt

# ── Icons ────────────────────────────────────────────────────────────────────

class AppIcon(QIcon):
    """QIcon loaded from myapp.resources.icons package."""
    def __init__(self, filename: str) -> None:
        with resources.as_file(resources.files("myapp.resources.icons").joinpath(filename)) as path:
            super().__init__(str(path))


class LogoIcon(AppIcon):
    def __init__(self) -> None:
        super().__init__(str("JV_logo.png"))

# ── Icons taken from Tabler Icons (MIT) https://tabler.io/icons ──────────────
# All icons are downloaded with size 24, stroke 2 and color #ffffff
class AppIconSVG(QIcon):
    """QIcon loaded from myapp.resources.icons package, colorised with
    palette(windowText)."""

    def __init__(
        self,
        filename: str,
        color_role: QPalette.ColorRole | None = QPalette.ColorRole.WindowText,
        color_name: str | None = None,
    ) -> None:
        super().__init__()

        with resources.as_file(
            resources.files("myapp.resources.icons").joinpath(filename)
            ) as path:
            with open(path, "r") as f:
                content = f.read()

        if color_name is not None:
            content = content.replace("#ffffff", color_name)
        elif color_role is not None:
            content = content.replace(
                "#ffffff", 
                QApplication.instance().palette().color(color_role).name())

        renderer = QSvgRenderer(QByteArray(content.encode()))
        pixmap = QPixmap(renderer.defaultSize())
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        self.addPixmap(pixmap)

class CalendarIcon(AppIconSVG):
    def __init__(
        self, 
        color_role=QPalette.ColorRole.WindowText, 
        color_name=None) -> None:
        super().__init__(
            "calendar.svg", color_role=color_role, color_name=color_name
            )


class SearchIcon(AppIconSVG):
    def __init__(
        self, 
        color_role=QPalette.ColorRole.WindowText, 
        color_name=None) -> None:
        super().__init__(
            "search.svg", color_role=color_role, color_name=color_name
            )


class EditIcon(AppIconSVG):
    def __init__(
        self, 
        color_role=QPalette.ColorRole.WindowText, 
        color_name=None) -> None:
        super().__init__(
            "edit.svg", color_role=color_role, color_name=color_name
            )


class FilterIcon(AppIconSVG):
    def __init__(
        self, 
        color_role=QPalette.ColorRole.WindowText, 
        color_name=None) -> None:
        super().__init__(
            "filter.svg", color_role=color_role, color_name=color_name
            )


class CloseIcon(AppIconSVG):
    def __init__(
        self, 
        color_role=QPalette.ColorRole.WindowText, 
        color_name=None) -> None:
        super().__init__(
            "close.svg", color_role=color_role, color_name=color_name
            )


class GithubSponsorIcon(AppIconSVG):
    def __init__(self):
        super().__init__("heart.svg", color_name="#EA4AAA") 