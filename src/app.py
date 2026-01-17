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
    QCompleter
)

from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QIcon

# TODO: guarantee that the icon exists
SEARCH_ICON = QIcon.fromTheme("edit-find")
# search_icon = QIcon(":/icons/search.svg")  # or a local file

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
        self.frame = QFrame(self)
        self.frame.setObjectName("cardFrame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)

        # Main layout for this widget
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.frame)

        # Layout inside the frame
        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # --- Top row: Company + status badge ---
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.company_label = QLabel(self.company)
        self.company_label.setObjectName("companyLabel")
        self.company_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.status_badge = QLabel(self.status)
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setContentsMargins(8, 2, 8, 2)

        top_row.addWidget(self.company_label)
        top_row.addStretch()
        top_row.addWidget(self.status_badge)

        # --- Middle row: Position + date applied ---
        self.position_label = QLabel(self.position)
        self.position_label.setObjectName("positionLabel")

        self.date_label = QLabel(f"Applied: {self.date_applied}")
        self.date_label.setObjectName("dateLabel")

        middle_row = QHBoxLayout()
        middle_row.setSpacing(8)
        middle_row.addWidget(self.position_label)
        middle_row.addStretch()
        middle_row.addWidget(self.date_label)

        # --- Bottom row: location + button bottom-right ---
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self.location_label = QLabel(self.location)
        self.location_label.setObjectName("locationLabel")

        bottom_row.addWidget(self.location_label)

        # spacer to push button to the right
        bottom_row.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.details_button = QPushButton("More details")
        self.details_button.setObjectName("detailsButton")
        bottom_row.addWidget(self.details_button)

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

    ROWS_COMPLETER = 2

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
        header_search_bar_layout = QVBoxLayout()
        header_search_bar_layout.setContentsMargins(0, 0, 0, 0)
        header_search_bar_layout.setSpacing(12)

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

        header_search_bar_layout.addLayout(header_layout, stretch=1)

        # --- Search bar ---
        # TODO: Figure out how to make the border round (StyleSheet is not working for that)
        # Maybe using a container widget could help
        self.searchbar = QLineEdit()
        self.searchbar.setPlaceholderText(
            "Search jobs by company, position, or location..."
            )
        self.searchbar.setClearButtonEnabled(True)
        self.searchbar.textChanged.connect(self.update_jobs_displayed)
        self.searchbar.addAction(
            SEARCH_ICON,
            QLineEdit.ActionPosition.LeadingPosition
            )

        self.searchbar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cfcfcf;
                border-radius: 18px;
                padding: 6px;
                font-size: 12px;
            }

            QLineEdit:focus {
                border: 1px solid #5a8dee;
            }""")

        # Adding Completer.
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.searchbar.setCompleter(self.completer)
        popup = self.completer.popup()
        popup.setUniformItemSizes(True)
        popup.setMaximumHeight((self.searchbar.fontMetrics().height() + 4) * self.ROWS_COMPLETER + 2)
        popup.setStyleSheet("""
            QListView {
                border: 1px solid #cccccc;
                border-radius: 2px;
                padding: 1px;
            }

            QListView::item {
                padding: 1px;
            }

            QListView::item:selected {
                border-radius: 2px;
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
            
            QListView::item:hover {
                border-radius: 2px;
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }""")
        popup.setWindowOpacity(0.1)

        header_search_bar_layout.addWidget(self.searchbar)

        main_layout.addLayout(header_search_bar_layout)

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

        self.query_all_job_apps()
        self.display_job_apps()

    def add_application(self):
        """ Adds an application to the scrollable body """
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

    def query_all_job_apps(self):
        """ Gets all jobs available. """

        # TODO: Ensure that there are not too many jobs that crashes everything
        # TODO: Get these from a database
        self.job_applications = [
            {
                "id": 1,
                "company": "Google",
                "position": "Data Scientist",
                "status": "Applied",
                "date_applied": "18/12/1992",
                "location": "London, UK",
                "contact_name": "",
                "contact_email": "",
                "salary": "50000",
                "url": "",
                "job_description": "Nice job",
                "notes": "",
                "last_update": ""
            },
            {
                "id": 2,
                "company": "Microsoft",
                "position": "Machine Learning Engineer",
                "status": "Applied",
                "date_applied": "20/01/1993",
                "location": "Cambridge, UK",
                "contact_name": "",
                "contact_email": "",
                "salary": "62000",
                "url": "",
                "job_description": "Work on ML systems",
                "notes": "",
                "last_update": ""
            },
            {
                "id": 3,
                "company": "Facebook",
                "position": "Data Analyst",
                "status": "Interview Scheduled",
                "date_applied": "05/03/1993",
                "location": "London, UK",
                "contact_name": "",
                "contact_email": "",
                "salary": "48000",
                "url": "",
                "job_description": "Analyse platform data",
                "notes": "",
                "last_update": ""
            },
            {
                "id": 4,
                "company": "Amazon",
                "position": "Business Intelligence Engineer",
                "status": "Applied",
                "date_applied": "11/04/1993",
                "location": "Manchester, UK",
                "contact_name": "",
                "contact_email": "",
                "salary": "55000",
                "url": "",
                "job_description": "Develop BI solutions",
                "notes": "",
                "last_update": ""
            },
            {
                "id": 5,
                "company": "IBM",
                "position": "AI Researcher",
                "status": "Rejected",
                "date_applied": "30/05/1993",
                "location": "London, UK",
                "contact_name": "",
                "contact_email": "",
                "salary": "70000",
                "url": "",
                "job_description": "Research AI models",
                "notes": "",
                "last_update": ""
            },]
        
        # TODO: Maybe these should be only the jobs that are added to self.job_card_widgets
        self.job_companies = [job["company"] for job in self.job_applications]
        self.job_positions = [job["position"] for job in self.job_applications]
        self.job_locations = [job["location"] for job in self.job_applications]
        self.completer_hints = self.job_companies + self.job_positions + self.job_locations
        self.update_completer_hints(self.completer_hints)

    def display_job_apps(self):
        self.job_card_widgets = [JobApplicationCard(**job) for job in self.job_applications]
        for widget in self.job_card_widgets:
            self.body_layout.insertWidget(self.body_layout.count() - 1, widget, alignment=Qt.AlignmentFlag.AlignTop)

    def update_jobs_displayed(self, text):
        for widget in self.job_card_widgets:
            # TODO: change this to all text not just the company and position
            if (text.lower() in widget.company.lower() 
                or text.lower() in widget.position.lower()
                or text.lower() in widget.location.lower()):
                widget.show()
            else:
                widget.hide()

    def update_completer_hints(self, hints: list[str]):
        self.completer.setModel(QStringListModel(hints))

app = QApplication([])
window = MainWindow()

window.show()
app.exec()
