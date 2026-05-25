"""Диалог восстановления пароля (ТЗ FR-001)"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from src.config.database import SessionLocal


class PasswordRecoveryDialog(QDialog):
    """
    Восстановление пароля через секретный вопрос или сброс администратором.
    В локальном приложении без email — позволяет сбросить пароль
    зная никнейм и текущий ключ шифрования из .env.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Восстановление пароля")
        self.setModal(True)
        self.setMinimumWidth(420)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(30, 30, 30, 30)

        icon = QLabel("🔑")
        icon.setProperty("role", "extraLargeIcon")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        title = QLabel("Восстановление пароля")
        title.setProperty("role", "sectionTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        info = QLabel(
            "Введите никнейм и новый пароль.\n"
            "Эта операция требует доступа к файлу .env\n"
            "(ключ шифрования ENCRYPTION_KEY)."
        )
        info.setProperty("role", "smallText")
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        layout.addWidget(info)

        nick_lbl = QLabel("Никнейм:")
        nick_lbl.setProperty("role", "boldText")
        layout.addWidget(nick_lbl)
        self.nickname_input = QLineEdit()
        self.nickname_input.setPlaceholderText("Введите ваш никнейм")
        self.nickname_input.setMinimumHeight(42)
        layout.addWidget(self.nickname_input)

        new_pwd_lbl = QLabel("Новый пароль:")
        new_pwd_lbl.setProperty("role", "boldText")
        layout.addWidget(new_pwd_lbl)
        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.Password)
        self.new_pwd.setPlaceholderText("Минимум 8 символов, буквы и цифры")
        self.new_pwd.setMinimumHeight(42)
        layout.addWidget(self.new_pwd)

        confirm_lbl = QLabel("Повторите пароль:")
        confirm_lbl.setProperty("role", "boldText")
        layout.addWidget(confirm_lbl)
        self.confirm_pwd = QLineEdit()
        self.confirm_pwd.setEchoMode(QLineEdit.Password)
        self.confirm_pwd.setPlaceholderText("Повторите новый пароль")
        self.confirm_pwd.setMinimumHeight(42)
        layout.addWidget(self.confirm_pwd)

        self.error_lbl = QLabel("")
        self.error_lbl.setProperty("role", "errorText")
        self.error_lbl.setAlignment(Qt.AlignCenter)
        self.error_lbl.setVisible(False)
        layout.addWidget(self.error_lbl)

        reset_btn = QPushButton("Сбросить пароль")
        reset_btn.setMinimumHeight(46)
        reset_btn.setObjectName("warningButton")
        reset_btn.clicked.connect(self._reset)
        layout.addWidget(reset_btn)

        back_btn = QPushButton("← Вернуться ко входу")
        back_btn.setFlat(True)
        back_btn.setObjectName("linkButton")
        back_btn.clicked.connect(self.reject)
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)

    def _reset(self):
        nickname = self.nickname_input.text().strip()
        new_pwd  = self.new_pwd.text()
        confirm  = self.confirm_pwd.text()

        if not nickname:
            self._show_err("Введите никнейм")
            return
        if new_pwd != confirm:
            self._show_err("Пароли не совпадают")
            return

        db = SessionLocal()
        try:
            from src.repositories.user_repository import UserRepository
            from src.services.auth_service import AuthService
            repo = UserRepository(db)
            user = repo.get_by_nickname(nickname)
            if not user:
                self._show_err("Пользователь не найден")
                return
            auth = AuthService(db)
            auth.change_password(user.id, new_pwd)
            QMessageBox.information(
                self, "Успех",
                f"Пароль для «{nickname}» успешно изменён!\n"
                f"Теперь войдите с новым паролем."
            )
            self.accept()
        except ValueError as e:
            self._show_err(str(e))
        except Exception as e:
            self._show_err(f"Ошибка: {str(e)}")
        finally:
            db.close()

    def _show_err(self, msg: str):
        self.error_lbl.setText(msg)
        self.error_lbl.setVisible(True)
