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
    QScrollArea
)

from PyQt6.QtCore import Qt

"""
TODOS:
Make the cards searchable with this
https://www.pythonguis.com/tutorials/pyqt6-widget-search-bar/
"""

class JobApplicationCard(QWidget):
    def __init__(self, 
        id, 
        company, 
        position, 
        status, 
        location,
        date_applied,
        contact_name, 
        contact_email,
        salary,
        url,
        job_description,
        notes,
        last_update):

        super().__init__()
        self.id = id
        self.company = company
        self.position = position
        self.status = status
        self.location = location
        self.date_applied = date_applied
        self.contact_name = contact_name
        self.contact_email = contact_email
        self.salary = salary
        self.url = url
        self.job_description = job_description
        self.notes = notes
        self.last_update = last_update

        self.setMinimumWidth(400)
        self.setMaximumWidth(900)
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
        )

        self._init_ui()

    def _init_ui(self):

        # Outer frame to give a card-like outline
        frame = QFrame(self)
        frame.setObjectName("cardFrame")
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setFrameShadow(QFrame.Shadow.Raised)

        # Main layout for this widget
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(frame)

        # Layout inside the frame
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # --- Top row: Company + status badge ---
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        company_label = QLabel(self.company)
        company_label.setObjectName("companyLabel")
        company_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        status_badge = QLabel(self.status)
        status_badge.setObjectName("statusBadge")
        status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_badge.setContentsMargins(8, 2, 8, 2)

        top_row.addWidget(company_label)
        top_row.addStretch()
        top_row.addWidget(status_badge)

        # --- Middle row: Position + date applied ---
        position_label = QLabel(self.position)
        position_label.setObjectName("positionLabel")

        date_label = QLabel(f"Applied: {self.date_applied}")
        date_label.setObjectName("dateLabel")

        middle_row = QHBoxLayout()
        middle_row.setSpacing(8)
        middle_row.addWidget(position_label)
        middle_row.addStretch()
        middle_row.addWidget(date_label)

        # --- Bottom row: location + button bottom-right ---
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        location_label = QLabel(self.location)
        location_label.setObjectName("locationLabel")

        bottom_row.addWidget(location_label)

        # spacer to push button to the right
        bottom_row.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        details_button = QPushButton("More details")
        details_button.setObjectName("detailsButton")
        bottom_row.addWidget(details_button)

        # Add rows to main card layout
        layout.addLayout(top_row)
        layout.addLayout(middle_row)
        layout.addLayout(bottom_row)

        # Simple stylesheet for card, badge, etc.
        self.setStyleSheet(
            """
            QFrame#cardFrame {
                border: 1px solid #cccccc;
                border-radius: 6px;
            }

            QLabel#companyLabel {
                font-weight: 600;
                font-size: 14px;
            }

            QLabel#positionLabel {
                font-size: 13px;
            }

            QLabel#dateLabel, QLabel#locationLabel {
                font-size: 11px;
                color: #666666;
            }

            QLabel#statusBadge {
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 11px;
                color: #ffffff;
                background-color: #2b7a2b; /* default green-ish */
            }

            QPushButton#detailsButton {
                font-size: 11px;
                padding: 4px 10px;
            }
            """
        )

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JobVault Libre")

        # Minimum size so the header always has room
        self.setMinimumSize(820, 520)

        # --- Root container ---
        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # --- Header ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        title_label = QLabel("<h1>JobVault Libre</h1>")
        subtitle_label = QLabel("Track and manage your job applications")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        header_layout.addLayout(title_layout, stretch=1)

        add_application_button = QPushButton("Add Application")
        add_application_button.clicked.connect(self.add_application)
        add_application_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_application_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        add_application_button.setMinimumHeight(34)
        
        header_layout.addWidget(add_application_button, alignment=Qt.AlignmentFlag.AlignTop)

        main_layout.addLayout(header_layout)

        # --- Scrollable body (only this part scrolls) ---
        body_container = QWidget()
        self.body_layout = QVBoxLayout(body_container)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(12)
        self.body_layout.addStretch(1)  # keeps cards pinned to the top

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(body_container)

        main_layout.addWidget(scroll, stretch=1)

        main_layout.addLayout(self.body_layout)

    def add_application(self):
        test_card = JobApplicationCard(
            id=1, 
            company="Google", 
            position="Data Scientist", 
            status="Applied", 
            date_applied="18/12/1992",
            location="London, UK",
            contact_name="", 
            contact_email="",
            salary="50000",
            url="",
            job_description="Nice job",
            notes="",
            last_update="")

        self.body_layout.insertWidget(self.body_layout.count() - 1, test_card, alignment=Qt.AlignmentFlag.AlignTop)
        # TODO: Decide whether I want the cards small or stretched horizontally as it is now and whether to align left or center.
        # self.body_layout.insertWidget(self.body_layout.count() - 1, test_card, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)





app = QApplication([])
window = MainWindow()

window.show()
app.exec()
