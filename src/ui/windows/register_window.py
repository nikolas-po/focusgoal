"""Окно регистрации (ТЗ FR-001.2, 152-ФЗ) - полная версия с адаптивом"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QMessageBox, QCheckBox, QProgressBar, QHBoxLayout,
    QScrollArea, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from src.config.database import SessionLocal
from src.services.auth_service import AuthService
from src.ui.windows.base_auth_window import BaseAuthWindow


class RegisterWindow(BaseAuthWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FocusGoal — Регистрация")
        self.setMinimumWidth(550)
        self.setMinimumHeight(750)
        self.resize(550, 800)
        self._setup_ui()

    def _setup_ui(self):
        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area для содержимого
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setProperty("role", "transparentScrollArea")

        container = QWidget()
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(14)
        layout.setContentsMargins(40, 30, 40, 30)

        # Заголовок
        layout.addWidget(self._create_logo("registerLogo"))
        layout.addWidget(self._create_title("Создать аккаунт", "registerTitle"))

        # Карточка
        card, cl = self._create_card("registerCard")

        # Никнейм
        cl.addWidget(self._create_label("Никнейм *", "registerLabel"))
        self.nickname_input = self._create_input("Минимум 3 символа")
        cl.addWidget(self.nickname_input)
        self.nick_hint = QLabel("")
        self.nick_hint.setProperty("role", "errorSmallText")
        cl.addWidget(self.nick_hint)

        # Email
        cl.addWidget(self._create_label("Email (необязательно)", "registerLabel"))
        self.email_input = self._create_input("example@mail.ru")
        cl.addWidget(self.email_input)

        # Пароль
        cl.addWidget(self._create_label("Пароль *", "registerLabel"))
        self.password_input = self._create_input("Минимум 8 символов", QLineEdit.Password)
        cl.addWidget(self.password_input)

        # Индикатор надёжности
        self.pwd_strength = QProgressBar()
        self.pwd_strength.setObjectName("pwdStrengthBar")
        self.pwd_strength.setRange(0, 4)
        self.pwd_strength.setTextVisible(False)
        self.pwd_strength.setMaximumHeight(6)
        cl.addWidget(self.pwd_strength)
        self.pwd_strength_label = QLabel("")
        self.pwd_strength_label.setProperty("role", "mutedSmallText")
        cl.addWidget(self.pwd_strength_label)

        # Повторить пароль
        cl.addWidget(self._create_label("Повторите пароль *", "registerLabel"))
        self.password2_input = self._create_input("Повторите пароль", QLineEdit.Password)
        cl.addWidget(self.password2_input)
        self.pwd2_hint = QLabel("")
        self.pwd2_hint.setProperty("role", "mutedSmallText")
        cl.addWidget(self.pwd2_hint)

        # Часовой пояс
        cl.addWidget(self._create_label("Часовой пояс", "registerLabel"))
        self.tz_combo = QComboBox()
        self.tz_combo.addItems([
            "UTC", "Europe/Moscow", "Europe/Kaliningrad",
            "Asia/Yekaterinburg", "Asia/Novosibirsk", "Asia/Krasnoyarsk",
            "Asia/Irkutsk", "Asia/Vladivostok", "Asia/Magadan", "Asia/Kamchatka",
        ])
        self.tz_combo.setCurrentIndex(1)
        self.tz_combo.setMinimumHeight(38)
        cl.addWidget(self.tz_combo)


        # Ошибки
        self.error_label = self._create_error_label("registerErrorLabel")
        cl.addWidget(self.error_label)

        # Кнопка регистрации
        reg_btn = self._create_button("Зарегистрироваться", "registerBtn")
        reg_btn.setMinimumHeight(48)
        cl.addWidget(reg_btn)

        layout.addWidget(card)
        layout.addStretch()

        # Кнопка назад
        back_row = QHBoxLayout()
        back_row.setAlignment(Qt.AlignCenter)
        back_row.addWidget(QLabel("Уже есть аккаунт?"))
        back_btn = self._create_button("Войти", "registerBackBtn")
        back_btn.setFlat(True)
        back_btn.setMinimumHeight(32)
        back_btn.clicked.connect(self.close)
        back_row.addWidget(back_btn)
        layout.addLayout(back_row)

        main_layout.addWidget(scroll)

        # События
        self.nickname_input.textChanged.connect(self._validate_nick)
        self.password_input.textChanged.connect(self._validate_pwd)
        self.password2_input.textChanged.connect(self._validate_pwd2)
        reg_btn.clicked.connect(self._register)

    def _validate_nick(self, text: str):
        stripped = text.strip()
        if stripped and len(stripped) < 3:
            self.nick_hint.setText("Минимум 3 символа")
        else:
            self.nick_hint.setText("")

    def _validate_pwd(self, text: str):
        score, label, color = _password_strength(text)
        self.pwd_strength.setValue(score)
        self.pwd_strength_label.setText(label)
        self.pwd_strength.setStyleSheet(
            f"QProgressBar::chunk {{ background: {color}; border-radius: 3px; }}"
        )
        self._validate_pwd2(self.password2_input.text())

    def _validate_pwd2(self, text: str):
        pwd = self.password_input.text()
        if not text:
            self.pwd2_hint.setText("")
        elif text == pwd:
            self.pwd2_hint.setText("✅ Пароли совпадают")
            self.pwd2_hint.setStyleSheet("font-size:11px; color:#4CAF50;")
        else:
            self.pwd2_hint.setText("❌ Пароли не совпадают")
            self.pwd2_hint.setStyleSheet("font-size:11px; color:#FF5252;")

    def _register(self):
        nickname  = self.nickname_input.text().strip()
        email     = self.email_input.text().strip() or None
        password  = self.password_input.text()
        password2 = self.password2_input.text()
        timezone  = self.tz_combo.currentText()

        if not nickname:
            self._show_error(self.error_label, "Введите никнейм")
            return
        if len(nickname) < 3:
            self._show_error(self.error_label, "Никнейм минимум 3 символа")
            return
        if not password:
            self._show_error(self.error_label, "Введите пароль")
            return
        if len(password) < 8:
            self._show_error(self.error_label, "Пароль минимум 8 символов")
            return
        if password != password2:
            self._show_error(self.error_label, "Пароли не совпадают")
            return

        db = SessionLocal()
        try:
            AuthService(db).register(nickname, password, email, timezone)
            QMessageBox.information(
                self,
                "Регистрация успешна",
                f"Аккаунт «{nickname}» создан!\n\nТеперь вы можете войти с этим никнеймом и паролем."
            )
            self.close()
        except ValueError as e:
            self._show_error(self.error_label, str(e))
        except Exception as e:
            self._show_error(self.error_label, f"Ошибка регистрации:\n{str(e)[:100]}")
        finally:
            db.close()


def _password_strength(pwd: str) -> tuple:
    """Вернуть (score 0-4, label, color) для индикатора надёжности."""
    if not pwd:
        return 0, "", "#cccccc"
    score = 0
    if len(pwd) >= 8: score += 1
    if len(pwd) >= 12: score += 1
    if any(c.isdigit() for c in pwd): score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in pwd): score += 1
    
    labels = {
        0: "❌ Очень слабый",
        1: "🔴 Слабый",
        2: "🟡 Средний",
        3: "🟢 Хороший",
        4: "✅ Отличный"
    }
    colors = {
        0: "#FF5252",
        1: "#FF7043",
        2: "#FFC107",
        3: "#66BB6A",
        4: "#4CAF50"
    }
    return score, labels[score], colors[score]