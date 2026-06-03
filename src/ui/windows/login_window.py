"""Окно входа (ТЗ FR-001.1)"""
import json, os
from pathlib import Path
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QLineEdit,
    QPushButton, QScrollArea, QWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from src.config.database import SessionLocal
from src.config.settings import Settings
from src.services.auth_service import AuthService
from src.ui.windows.base_auth_window import BaseAuthWindow
from src.utils.encryption import decrypt_bytes, encrypt_bytes


class LoginWindow(BaseAuthWindow):
    def __init__(self, settings: Settings = None, parent=None):
        super().__init__(parent)
        self.settings = settings or Settings()
        self.setWindowTitle("FocusGoal — Вход")
        self._remember_file = self.settings.BASE_DIR / ".focusgoal_remember.json"
        self._block_timer = None   # QTimer для обратного отсчёта блокировки
        self._setup_ui()
        self._load_remembered()

    # Запомни меня

    def _load_remembered(self):
        if not self._remember_file.exists(): return
        try:
            raw = self._remember_file.read_bytes()
            if self.settings.ENCRYPTION_KEY:
                try: raw = decrypt_bytes(raw, self.settings.ENCRYPTION_KEY)
                except: pass
            d = json.loads(raw.decode())
            self.nickname_input.setText(d.get("nickname",""))
            self.password_input.setText(d.get("password",""))
            self.remember_me.setChecked(True)
        except Exception as e:
            self.logger.warning(f"Remember: {e}")

    def _save_remembered(self, nick: str, pwd: str):
        if self.remember_me.isChecked():
            try:
                payload = json.dumps({"nickname": nick, "password": pwd}).encode()
                if self.settings.ENCRYPTION_KEY:
                    payload = encrypt_bytes(payload, self.settings.ENCRYPTION_KEY)
                self._remember_file.write_bytes(payload)
                try: os.chmod(self._remember_file, 0o600)
                except: pass
            except Exception as e:
                self.logger.warning(f"Save remember: {e}")
        else:
            LoginWindow.clear_remembered(self.settings)

    @staticmethod
    def clear_remembered(settings: Settings = None):
        f = (settings or Settings()).BASE_DIR / ".focusgoal_remember.json"
        try:
            if f.exists(): f.unlink()
        except: pass

    # Интерфейс

    def _setup_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(420, 540)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignTop)
        scroll.setProperty("role", "transparentBackground")
        container = QWidget()
        container.setMaximumWidth(720)
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(14)
        layout.setContentsMargins(30, 24, 30, 24)

        layout.addWidget(self._create_logo("loginLogo"))
        layout.addWidget(self._create_title("FocusGoal", "loginTitle"))

        subtitle = QLabel("Система управления целями и привычками")
        subtitle.setObjectName("loginSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        layout.addSpacing(8)

        card, cl = self._create_card("loginCard")
        card.setMaximumWidth(640)

        cl.addWidget(self._create_label("Никнейм", "loginLabel"))
        self.nickname_input = self._create_input("Введите никнейм")
        self.nickname_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        cl.addWidget(self.nickname_input)

        cl.addWidget(self._create_label("Пароль", "loginLabel"))
        self.password_input = self._create_input("Введите пароль", QLineEdit.Password)
        self.password_input.returnPressed.connect(self._login)
        cl.addWidget(self.password_input)

        self.remember_me = QCheckBox("Запомнить меня")
        self.remember_me.setObjectName("loginCheckbox")
        cl.addWidget(self.remember_me)

        forgot_btn = self._create_button("Забыли пароль?", "loginForgotBtn")
        forgot_btn.setFlat(True)
        forgot_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        forgot_btn.clicked.connect(self._open_recovery)
        cl.addWidget(forgot_btn, alignment=Qt.AlignRight)

        self.error_label = self._create_error_label("loginErrorLabel")
        cl.addWidget(self.error_label)

        # Обратный отсчёт при блокировке
        self.countdown_label = QLabel("")
        self.countdown_label.setObjectName("loginErrorLabel")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.hide()
        cl.addWidget(self.countdown_label)

        self.login_btn = self._create_button("Войти", "loginBtn")
        self.login_btn.clicked.connect(self._login)
        cl.addWidget(self.login_btn)

        layout.addWidget(card)

        

        reg_row = QHBoxLayout()
        reg_row.setAlignment(Qt.AlignCenter)
        reg_row.addWidget(QLabel("Нет аккаунта?"))
        reg_btn = self._create_button("Зарегистрироваться", "loginRegBtn")
        reg_btn.setFlat(True)
        reg_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        reg_btn.clicked.connect(self._open_register)
        reg_row.addWidget(reg_btn)
        layout.addLayout(reg_row)

        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        layout.addStretch()

    # Действия

    def _login(self):
        if not self.login_btn.isEnabled(): return
        nick = self.nickname_input.text().strip()
        pwd  = self.password_input.text()
        if not nick or not pwd:
            self._show_error(self.error_label, "Введите никнейм и пароль"); return
        self.logger.info(f"Попытка входа: {nick}")
        db = SessionLocal()
        try:
            user_data = AuthService(db).login(nick, pwd)
            self._save_remembered(nick, pwd)
            self.logger.info(f"Вход успешен: {nick} (ID={user_data['id']})")
            self._open_main(user_data)
        except ValueError as e:
            msg = str(e)
            self._show_error(self.error_label, msg)
            if "заблокирован" in msg.lower() or "подождите" in msg.lower():
                self._start_block_countdown(30)
        except Exception as e:
            self._show_error(self.error_label, f"Ошибка подключения: {e}")
        finally:
            db.close()

    def _start_block_countdown(self, seconds: int):
        """Показать обратный отсчёт и заблокировать кнопку входа."""
        self._remaining = seconds
        self.login_btn.setEnabled(False)
        self.countdown_label.show()
        self._update_countdown()
        self._block_timer = QTimer(self)
        self._block_timer.timeout.connect(self._tick_countdown)
        self._block_timer.start(1000)

    def _tick_countdown(self):
        self._remaining -= 1
        if self._remaining <= 0:
            self._block_timer.stop()
            # layout.addStretch() 
            self.countdown_label.hide()
            self.error_label.clear()
        else:
            self._update_countdown()

    def _update_countdown(self):
        self.countdown_label.setText(f"Подождите {self._remaining} сек. перед следующей попыткой")

    def _open_main(self, user_data: dict):
        from PyQt5.QtWidgets import QApplication
        from src.main import apply_saved_theme, safe_raise
        from src.ui.windows.main_window import MainWindow
        from src.services.notification_service import NotificationService
        self.main_window = MainWindow(user_data)
        apply_saved_theme(QApplication.instance(), user_data["id"])
        try:
            NotificationService.start_scheduler()
            notif_service = NotificationService(SessionLocal(), user_data["id"])
            notif_service.schedule_notifications(interval_minutes=1)
        except Exception:
            pass
        # Автоматически установить systemd-таймер, если ещё не установлен.
        # Это обеспечивает приход уведомлений даже при закрытом приложении.
        try:
            from src.services.system_notifications import NotificationInstaller
            if not NotificationInstaller.is_installed():
                NotificationInstaller.install()
        except Exception:
            pass
        self.main_window.show()
        safe_raise(self.main_window)
        self.close()

    def _open_register(self):
        from src.main import apply_theme, safe_raise
        from src.config import theme_state
        from src.ui.windows.register_window import RegisterWindow
        self.reg_window = RegisterWindow(self)
        self.reg_window.show()
        apply_theme(theme_state.current_theme, theme_state.current_font_size)
        safe_raise(self.reg_window)

    def _open_recovery(self):
        try:
            from src.ui.dialogs.password_recovery_dialog import PasswordRecoveryDialog
            PasswordRecoveryDialog(self).exec_()
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Восстановление пароля",
                "Обратитесь к администратору системы или\n"
                "используйте инструменты командной строки.")

    def showEvent(self, event):
        super().showEvent(event)
        try:
            scroll = self.findChild(QScrollArea)
            card = self.findChild(QWidget, 'loginCard')
            btn = self.findChild(QPushButton, 'loginBtn')
            if scroll and card:
                scroll.ensureWidgetVisible(card)
            if scroll and btn:
                scroll.ensureWidgetVisible(btn)
        except Exception:
            pass
