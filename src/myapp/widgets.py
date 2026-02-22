from importlib import resources

from PyQt6.QtWidgets import (
    QTextEdit,
    QAbstractSpinBox,
    QDateEdit,
    QComboBox,
    )
from PyQt6.QtGui import (
    QTextDocumentFragment, 
    QTextCursor, 
    QTextCharFormat, 
    QPalette,
    )
from PyQt6.QtCore import QDate, QMimeData

class BaseColourTextEdit(QTextEdit):

    def insertFromMimeData(self, source: QMimeData):
        cursor = self.textCursor()
        cursor.beginEditBlock()

        start = cursor.selectionStart() if cursor.hasSelection() else cursor.position()

        if source.hasHtml():
            frag = QTextDocumentFragment.fromHtml(source.html())
            cursor.insertFragment(frag)
        else:
            cursor.insertText(source.text())

        end = cursor.position()

        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)

        fmt = QTextCharFormat()
        fmt.setForeground(self.palette().color(QPalette.ColorRole.Text))
        cursor.mergeCharFormat(fmt)

        self.mergeCurrentCharFormat(fmt)

        cursor.endEditBlock()


class NoScrollDateEdit(QDateEdit):
    def __init__(self, parent=None, date=None):
        super().__init__(parent)
        self.setDisplayFormat("dd/MM/yyyy")
        self.setCalendarPopup(True)
        if isinstance(date, QDate):
            self.setDate(date)
        else:
            self.setDate(QDate.currentDate())
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        with resources.as_file(resources.files("myapp.resources.icons").joinpath("calendar.svg")) as path:
            CALENDAR_ICON_PATH = str(path)
            self.setStyleSheet(
                f"""
                QDateEdit::down-arrow {{
                    image: url("{CALENDAR_ICON_PATH}");
                    width: 16px;
                    height: 16px;
                }}
                QDateEdit::drop-down {{
                    border: none;
                    padding-right: 6px;
                }}
                QDateEdit {{
                    background-color: palette(base);
                    color: palette(windowText);
                    border: 1px solid palette(mid);
                    border-radius: 6px;
                    padding: 6px;
                    min-width: 88px;
                }}
                QDateEdit:focus {{
                    border: 1px solid palette(highlight);
                }}
                """
            )

    def wheelEvent(self, event):
        event.ignore()


class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()