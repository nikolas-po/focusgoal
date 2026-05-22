"""Базовое окно авторизации"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from src.config.logging_config import setup_logging


class BaseAuthWindow(QWidget):
    """Базовое окно для входа и регистрации"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = setup_logging()
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_DeleteOnClose)

    @staticmethod
    def _create_logo(object_name: str) -> QLabel:
        """Создать лого"""
        logo = QLabel("🎯")
        logo.setObjectName(object_name)
        logo.setAlignment(Qt.AlignCenter)
        logo.setFont(QFont("Arial", 48))
        return logo

    @staticmethod
    def _create_title(text: str, object_name: str) -> QLabel:
        """Создать заголовок"""
        title = QLabel(text)
        title.setObjectName(object_name)
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        return title

    @staticmethod
    def _create_label(text: str, object_name: str = "") -> QLabel:
        """Создать обычный текстовый label"""
        label = QLabel(text)
        if object_name:
            label.setObjectName(object_name)
        label.setFont(QFont("Arial", 12))
        return label

    @staticmethod
    def _create_input(placeholder: str = "", mode=QLineEdit.Normal) -> QLineEdit:
        """Создать поле ввода"""
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setEchoMode(mode)
        inp.setMinimumHeight(42)
        inp.setFont(QFont("Arial", 12))
        return inp

    @staticmethod
    def _create_button(text: str, object_name: str) -> QPushButton:
        """Создать кнопку"""
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.setMinimumHeight(48)
        button.setFont(QFont("Arial", 12, QFont.Bold))
        button.setCursor(__import__('PyQt5.QtCore', fromlist=['Qt']).Qt.PointingHandCursor)
        return button

    @staticmethod
    def _create_card(object_name: str) -> tuple:
        """Создать карточку (frame + layout)"""
        card = QFrame()
        card.setObjectName(object_name)
        card.setMinimumWidth(350)
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 25, 30, 25)
        return card, layout

    @staticmethod
    def _create_error_label(object_name: str = "authErrorLabel") -> QLabel:
        """Создать label для ошибок"""
        error = QLabel()
        error.setObjectName(object_name)
        error.setAlignment(Qt.AlignCenter)
        error.setMinimumHeight(24)
        error.setWordWrap(True)
        error.setVisible(False)
        return error

    @staticmethod
    def _show_error(error_label: QLabel, message: str):
        """Показать ошибку"""
        error_label.setText(message)
        error_label.setVisible(True)

    @staticmethod
    def _hide_error(error_label: QLabel):
        """Скрыть ошибку"""
        error_label.setText("")
        error_label.setVisible(False)