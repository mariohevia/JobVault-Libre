from importlib import resources
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QFrame,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QPalette, QColor, QIcon

class SupportPage(QWidget):
    def __init__(self, palette: QPalette, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("supportPage")

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(24)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)

        title = QLabel("Support This Project")
        title.setObjectName("supportTitle")
        header_layout.addWidget(title)

        subtitle = QLabel("Help keep this project free, open-source, and actively maintained")
        subtitle.setObjectName("supportSubtitle")
        header_layout.addWidget(subtitle)

        root.addLayout(header_layout)

        # Main content card
        card = QFrame()
        card.setObjectName("supportCard")
        
        # Add subtle shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(24)

        # About section
        about_text = (
            "Hey! This is a free, open-source app I built to make tracking job applications "
            "easier. Everything runs locally on your computer with no cloud services, no tracking, "
            "no funny business.\n\n"
            "I develop this in my free time, and it'll always be free with no paywalls or "
            "subscriptions. Your data? It never leaves your machine.\n\n"
            "If you're finding this useful and want to help keep it going, any support is "
            "hugely appreciated. It helps me carve out time to maintain and improve the app "
            "for everyone."
        )

        about = QLabel(about_text)
        about.setObjectName("supportBody")
        about.setWordWrap(True)
        about.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        card_layout.addWidget(about)

        # Separator line
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        card_layout.addWidget(separator)

        # Support options label
        support_label = QLabel("Support Options")
        support_label.setObjectName("supportSectionLabel")
        card_layout.addWidget(support_label)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        # Buy Me a Coffee button
        self.bmac_btn = QPushButton("☕ Buy Me a Coffee")
        self.bmac_btn.setObjectName("supportPrimaryButton")
        self.bmac_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bmac_btn.setMinimumHeight(44)
        self.bmac_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://buymeacoffee.com/mario.hevia"))
        )

        # GitHub sponsor button
        with resources.as_file(resources.files("myapp.resources.icons").joinpath("heart.png")) as path:
            GITHUB_ICON_PATH = str(path).replace("\\", "/")
        self.github_sup_btn = QPushButton(" Support on GitHub")
        self.github_sup_btn.setObjectName("supportSecondaryButton")
        self.github_sup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.github_sup_btn.setMinimumHeight(44)
        self.github_sup_btn.setIcon(QIcon(GITHUB_ICON_PATH))  # Add this line
        self.github_sup_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/sponsors/mariohevia"))
        )

        # GitHub button
        self.github_btn = QPushButton("⭐ Star on GitHub")
        self.github_btn.setObjectName("supportSecondaryButton")
        self.github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.github_btn.setMinimumHeight(44)
        self.github_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/mariohevia/JobVault-Libre"))
        )

        buttons_layout.addWidget(self.bmac_btn)
        buttons_layout.addWidget(self.github_sup_btn)
        buttons_layout.addWidget(self.github_btn)

        card_layout.addLayout(buttons_layout)

        # Thank you note
        thank_you = QLabel("Thank you for your support! 💙")
        thank_you.setObjectName("thankYouLabel")
        thank_you.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(thank_you)

        root.addWidget(card)

        # Feature highlights section
        features_layout = QHBoxLayout()
        features_layout.setSpacing(16)

        feature_items = [
            ("🔒", "Privacy First", "All data stays local"),
            ("💰", "100% Free", "No paid features"),
            ("🌐", "Open Source", "Community driven")
        ]

        for icon, title_text, desc in feature_items:
            feature_card = self._create_feature_card(icon, title_text, desc)
            features_layout.addWidget(feature_card)

        root.addLayout(features_layout)
        root.addStretch(1)

        self.setStyleSheet(self._get_stylesheet())

    def _create_feature_card(self, icon: str, title: str, description: str) -> QFrame:
        """Create a small feature highlight card"""
        card = QFrame()
        card.setObjectName("featureCard")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel(icon)
        icon_label.setObjectName("featureIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setObjectName("featureTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setObjectName("featureDesc")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        return card

    def _get_stylesheet(self) -> str:
        """Return the complete stylesheet for the support page"""
        return """
        QWidget#supportPage {
            background: palette(window);
            color: palette(windowText);
        }

        QLabel#supportTitle {
            font-size: 28px;
            font-weight: 700;
            color: palette(windowText);
            letter-spacing: -0.5px;
        }

        QLabel#supportSubtitle {
            color: palette(mid);
            font-size: 14px;
            font-weight: 400;
        }

        QFrame#supportCard {
            background: palette(base);
            border: 1px solid palette(midlight);
            border-radius: 16px;
        }

        QLabel#supportBody {
            font-size: 14px;
            line-height: 1.6;
            color: palette(windowText);
        }

        QFrame#separator {
            background: palette(midlight);
            border: none;
        }

        QLabel#supportSectionLabel {
            font-size: 15px;
            font-weight: 600;
            color: palette(windowText);
            margin-bottom: 4px;
        }

        QLabel#thankYouLabel {
            font-size: 13px;
            font-style: italic;
            margin-top: 8px;
        }

        QFrame#featureCard {
            background: palette(base);
            border: 1px solid palette(midlight);
            border-radius: 12px;
            padding: 12px;
        }

        QFrame#featureCard:hover {
            border: 1px solid palette(mid);
            background: palette(light);
        }

        QLabel#featureIcon {
            font-size: 32px;
        }

        QLabel#featureTitle {
            font-size: 13px;
            font-weight: 600;
            color: palette(windowText);
        }

        QLabel#featureDesc {
            font-size: 11px;
            color: palette(mid);
        }
        """