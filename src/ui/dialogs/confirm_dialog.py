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
        icon.setProperty("role", "largeIcon")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignCenter)
        msg.setProperty("role", "bodyText")
        layout.addWidget(msg)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setText(confirm_text)
        ok_btn.setObjectName("dangerButton")
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("Отмена")
        cancel_btn.setObjectName("cancelButton")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
