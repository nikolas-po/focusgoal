"""Диалог подтверждения действия"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QDialogButtonBox, QHBoxLayout
)
from PyQt5.QtCore import Qt


class ConfirmDialog(QDialog):
    def __init__(self, message: str, title: str = "Подтверждение",
                 confirm_text: str = "Подтвердить", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        icon = QLabel("⚠️")
        icon.setStyleSheet("font-size: 44px;")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet("font-size: 14px;")
        layout.addWidget(msg)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Ok).setText(confirm_text)
        buttons.button(QDialogButtonBox.Ok).setStyleSheet(
            "background: #FF5252; color: white; min-height: 36px;"
        )
        buttons.button(QDialogButtonBox.Cancel).setText("Отмена")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
