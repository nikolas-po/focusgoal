"""Диалог для ввода пароля администратора при запуске от админа (pkexec)"""
import subprocess
import os
import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import logging


class AdminPasswordDialog(QDialog):
    """Диалог для ввода пароля администратора через GUI вместо терминала"""
    
    def __init__(self, parent=None, app_args=None):
        super().__init__(parent)
        self.app_args = app_args or []
        self.logger = logging.getLogger(__name__)
        self.password = None
        self.setWindowTitle("Пароль администратора")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._setup_ui()

    def _setup_ui(self):
        """Создать UI элементы"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        title = QLabel("Требуется пароль администратора")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # Описание
        info = QLabel(
            "Приложение требует административные права.\n"
            "Введите пароль администратора:"
        )
        info.setProperty("role", "mutedSmallText")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Поле ввода пароля
        pwd_layout = QHBoxLayout()
        pwd_label = QLabel("Пароль:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.returnPressed.connect(self._try_password)
        pwd_layout.addWidget(pwd_label, 0)
        pwd_layout.addWidget(self.password_input, 1)
        layout.addLayout(pwd_layout)

        # Ошибка
        self.error_label = QLabel()
        self.error_label.setProperty("role", "errorTextSmall")
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumHeight(38)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("Ввести")
        ok_btn.setMinimumHeight(38)
        ok_btn.setMinimumWidth(100)
        ok_btn.setObjectName("primaryButton")
        ok_btn.clicked.connect(self._try_password)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

        self.password_input.setFocus()

    def _try_password(self):
        """Попытаться использовать пароль для pkexec"""
        password = self.password_input.text()
        
        if not password:
            self._show_error("Введите пароль")
            return

        self.logger.info("Попытка запуска приложения от администратора")
        
        try:
            # Подготовить окружение
            preserved_env = os.environ.copy()
            for key in (
                "DISPLAY", "XAUTHORITY", "WAYLAND_DISPLAY",
                "QT_QPA_PLATFORM", "XDG_RUNTIME_DIR", "HOME"
            ):
                if key not in preserved_env:
                    preserved_env[key] = os.environ.get(key, "")

            # Подготовить команду
            launch = [sys.executable]
            if len(sys.argv) > 0 and sys.argv[0].endswith(".py"):
                launch = [sys.executable, os.path.abspath(sys.argv[0])]
            else:
                launch = [sys.executable, "-m", "src.main"]
            
            launch += self.app_args

            # Использовать sudo -S для передачи пароля через stdin
            cmd = ["sudo", "-S", "-E"] + launch
            
            # Запустить процесс с пароля через stdin
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=preserved_env,
                text=True
            )
            
            # Отправить пароль
            stdout, stderr = process.communicate(input=password + "\n", timeout=5)
            
            if process.returncode == 0:
                self.logger.info("Приложение запущено от администратора")
                self.password = password
                self.accept()
            else:
                error_msg = stderr.strip() if stderr else "Неверный пароль"
                if "password is required" in error_msg.lower() or "incorrect password" in error_msg.lower():
                    error_msg = "Неверный пароль"
                self._show_error(error_msg)
                self.logger.warning(f"Ошибка входа администратора: {error_msg}")
                self.password_input.clear()
                self.password_input.setFocus()
        
        except subprocess.TimeoutExpired:
            self._show_error("Истекло время ожидания")
            self.logger.error("Истекло время ожидания ответа sudo")
            process.kill()
        except Exception as e:
            error_msg = str(e)
            self._show_error(f"Ошибка: {error_msg}")
            self.logger.error(f"Ошибка запуска от администратора: {e}")

    def _show_error(self, msg: str):
        """Показать сообщение об ошибке"""
        self.error_label.setText(msg)
        self.error_label.setVisible(True)

    def get_password(self) -> str:
        """Вернуть введенный пароль"""
        return self.password
