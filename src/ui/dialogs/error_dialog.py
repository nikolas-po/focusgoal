"""Диалог отображения ошибок"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt


class ErrorDialog(QDialog):
    def __init__(self, title: str, message: str,
                 details: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(25, 25, 25, 25)

        icon = QLabel("❌")
        icon.setProperty("role", "largeIcon")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        title_lbl = QLabel(title)
        title_lbl.setProperty("role", "sectionHeader")
        title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setProperty("role", "bodyText")
        layout.addWidget(msg_lbl)

        if details:
            det_lbl = QLabel("Детали:")
            det_lbl.setProperty("role", "boldText")
            layout.addWidget(det_lbl)
            det_text = QTextEdit()
            det_text.setReadOnly(True)
            det_text.setPlainText(details)
            det_text.setMaximumHeight(120)
            layout.addWidget(det_text)

        hints = QLabel(
            "Рекомендации:\n"
            "• Проверьте подключение к базе данных\n"
            "• Проверьте свободное место на диске\n"
            "• Попробуйте восстановить из резервной копии"
        )
        hints.setProperty("role", "mutedSmallText")
        hints.setWordWrap(True)
        layout.addWidget(hints)

        ok_btn = QPushButton("OK")
        ok_btn.setMinimumHeight(40)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
