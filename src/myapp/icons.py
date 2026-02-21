from importlib import resources

from PyQt6.QtGui import QPixmap, QIcon

# ── Icons ────────────────────────────────────────────────────────────────────

class AppIcon(QIcon):
    """QIcon loaded from myapp.resources.icons package."""
    def __init__(self, filename: str) -> None:
        with resources.as_file(resources.files("myapp.resources.icons").joinpath(filename)) as path:
            super().__init__(str(path))


class LogoIcon(AppIcon):
    def __init__(self) -> None:
        super().__init__(str("JV_logo.png"))

# ── Pixmaps ──────────────────────────────────────────────────────────────────

class AppPixmap(QPixmap):
    """QPixmap loaded from myapp.resources.icons package."""
    def __init__(self, filename: str) -> None:
        with resources.as_file(resources.files("myapp.resources.icons").joinpath(filename)) as path:
            super().__init__(str(path))


class LogoPixmap(AppPixmap):
    def __init__(self) -> None:
        super().__init__(str("JV_logo.png"))
