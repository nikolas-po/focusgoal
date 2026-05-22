"""Окно настроек (ТЗ FR-008)"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QComboBox, QLineEdit,
    QCheckBox, QTimeEdit, QSpinBox, QTabWidget,
    QScrollArea, QMessageBox, QFormLayout
)
from PyQt5.QtCore import Qt, QTime
from src.config.database import SessionLocal
from src.config.settings import Settings


class SettingsWindow(QWidget):
    def __init__(self, user_id: int = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.settings = Settings()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("Настройки")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        tabs = QTabWidget()

        # Вкладка: Внешний вид
        appearance_tab = QWidget()
        al = QVBoxLayout(appearance_tab)
        al.setSpacing(15)
        al.setContentsMargins(15, 15, 15, 15)

        theme_g = QGroupBox("Тема оформления")
        tl = QFormLayout(theme_g)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная"])
        self.theme_combo.setMinimumHeight(38)
        tl.addRow("Тема:", self.theme_combo)
        al.addWidget(theme_g)

        font_g = QGroupBox("Размер шрифта")
        fl = QFormLayout(font_g)
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Маленький (12px)", "Средний (14px)", "Большой (16px)"])
        self.font_combo.setCurrentIndex(1)
        self.font_combo.setMinimumHeight(38)
        fl.addRow("Размер:", self.font_combo)
        al.addWidget(font_g)

        theme_apply_btn = QPushButton("Применить тему")
        theme_apply_btn.setMinimumHeight(42)
        theme_apply_btn.clicked.connect(self._apply_theme)
        al.addWidget(theme_apply_btn)
        al.addStretch()
        tabs.addTab(appearance_tab, "Внешний вид")

        # Вкладка: Уведомления
        notif_tab = QWidget()
        nl = QVBoxLayout(notif_tab)
        nl.setSpacing(12)
        nl.setContentsMargins(15, 15, 15, 15)

        notif_g = QGroupBox("Уведомления")
        nfl = QFormLayout(notif_g)
        self.notif_check = QCheckBox("Включить уведомления")
        self.notif_check.setChecked(True)
        nfl.addRow(self.notif_check)

        self.notif_goals_check = QCheckBox("Уведомления о целях")
        self.notif_goals_check.setChecked(True)
        nfl.addRow(self.notif_goals_check)

        self.notif_habits_check = QCheckBox("Уведомления о привычках")
        self.notif_habits_check.setChecked(True)
        nfl.addRow(self.notif_habits_check)

        self.notif_focus_check = QCheckBox("Уведомления о фокус-сессиях")
        self.notif_focus_check.setChecked(True)
        nfl.addRow(self.notif_focus_check)
        nl.addWidget(notif_g)

        quiet_g = QGroupBox("Тихий режим (не беспокоить)")
        qfl = QFormLayout(quiet_g)
        self.quiet_check = QCheckBox("Включить тихий режим")
        qfl.addRow(self.quiet_check)
        self.quiet_start = QTimeEdit()
        self.quiet_start.setTime(QTime(22, 0))
        self.quiet_start.setMinimumHeight(38)
        qfl.addRow("Начало:", self.quiet_start)
        self.quiet_end = QTimeEdit()
        self.quiet_end.setTime(QTime(8, 0))
        self.quiet_end.setMinimumHeight(38)
        qfl.addRow("Конец:", self.quiet_end)
        nl.addWidget(quiet_g)
        # Фоновые уведомления через systemd
        sys_g = QGroupBox("Фоновые уведомления (без приложения)")
        sys_l = QVBoxLayout(sys_g)
        sys_desc = QLabel(
            "Установите systemd-таймер — уведомления о целях и привычках\n"
            "будут приходить каждые 5 минут, даже если приложение закрыто."
        )
        sys_desc.setWordWrap(True)
        sys_desc.setStyleSheet("font-size:11px; color:palette(mid);")
        sys_l.addWidget(sys_desc)
        btn_row = QHBoxLayout()
        self.sys_install_btn = QPushButton("⚙️ Установить таймер")
        self.sys_install_btn.setMinimumHeight(38)
        self.sys_install_btn.clicked.connect(self._install_sys_notif)
        btn_row.addWidget(self.sys_install_btn)
        self.sys_uninstall_btn = QPushButton("🗑 Удалить таймер")
        self.sys_uninstall_btn.setMinimumHeight(38)
        self.sys_uninstall_btn.clicked.connect(self._uninstall_sys_notif)
        btn_row.addWidget(self.sys_uninstall_btn)
        sys_l.addLayout(btn_row)
        self.sys_status_lbl = QLabel("")
        self.sys_status_lbl.setStyleSheet("font-size:11px;")
        sys_l.addWidget(self.sys_status_lbl)
        nl.addWidget(sys_g)

        nl.addStretch()
        tabs.addTab(notif_tab, "Уведомления")
        self._refresh_sys_status()

        # Вкладка: Безопасность
        sec_tab = QWidget()
        sl = QVBoxLayout(sec_tab)
        sl.setSpacing(12)
        sl.setContentsMargins(15, 15, 15, 15)

        pwd_g = QGroupBox("Изменить пароль")
        pfl = QFormLayout(pwd_g)
        self.old_pwd = QLineEdit()
        self.old_pwd.setEchoMode(QLineEdit.Password)
        self.old_pwd.setMinimumHeight(38)
        pfl.addRow("Текущий пароль:", self.old_pwd)
        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.Password)
        self.new_pwd.setMinimumHeight(38)
        pfl.addRow("Новый пароль:", self.new_pwd)
        self.new_pwd2 = QLineEdit()
        self.new_pwd2.setEchoMode(QLineEdit.Password)
        self.new_pwd2.setMinimumHeight(38)
        pfl.addRow("Повторите пароль:", self.new_pwd2)

        self.pwd_match_label = QLabel("")
        self.pwd_match_label.setStyleSheet("font-size:11px; color:#666;")
        pfl.addRow("", self.pwd_match_label)
        self.new_pwd.textChanged.connect(self._check_pwd_match)
        self.new_pwd2.textChanged.connect(self._check_pwd_match)
        sl.addWidget(pwd_g)

        change_pwd_btn = QPushButton("Изменить пароль")
        change_pwd_btn.setMinimumHeight(42)
        change_pwd_btn.clicked.connect(self._change_password)
        sl.addWidget(change_pwd_btn)

        # Удаление данных
        del_g = QGroupBox("Удаление данных (152-ФЗ)")
        del_l = QVBoxLayout(del_g)
        del_info = QLabel(
            "Вы можете запросить удаление всех ваших данных.\n"
            "Данные будут удалены в течение 24 часов."
        )
        del_info.setStyleSheet("color: #666; font-size: 12px;")
        del_info.setWordWrap(True)
        del_l.addWidget(del_info)
        del_btn = QPushButton("Запросить удаление данных")
        del_btn.setObjectName("dangerButton")
        del_btn.setMinimumHeight(42)
        del_btn.clicked.connect(self._request_deletion)
        del_l.addWidget(del_btn)
        sl.addWidget(del_g)
        sl.addStretch()
        tabs.addTab(sec_tab, "Безопасность")

        # Вкладка: О приложении
        about_tab = QWidget()
        abl = QVBoxLayout(about_tab)
        abl.setAlignment(Qt.AlignTop)
        abl.setContentsMargins(15, 15, 15, 15)

        logo = QLabel("🎯")
        logo.setStyleSheet("font-size: 64px;")
        logo.setAlignment(Qt.AlignCenter)
        abl.addWidget(logo)

        app_name = QLabel("FocusGoal")
        app_name.setStyleSheet("font-size: 24px; font-weight: bold; color: #4CAF50;")
        app_name.setAlignment(Qt.AlignCenter)
        abl.addWidget(app_name)

        version = QLabel("Версия 1.0.0")
        version.setStyleSheet("color: #888; font-size: 13px;")
        version.setAlignment(Qt.AlignCenter)
        abl.addWidget(version)

        desc = QLabel(
            "Система управления личными целями, привычками\n"
            "и продуктивностью с функцией блокировки отвлекающих приложений.\n\n"
            "© 2024 FocusGoal Team\n"
            "Лицензия: MIT"
        )
        desc.setStyleSheet("font-size: 12px; color: #666;")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        abl.addWidget(desc)
        abl.addStretch()
        tabs.addTab(about_tab, "ℹ О приложении")

        layout.addWidget(tabs)

        # Кнопка сохранения
        save_btn = QPushButton("Сохранить настройки")
        save_btn.setMinimumHeight(46)
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        container.setLayout(layout)
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def _load_settings(self):
        if not self.user_id:
            return
        from src.main import _hostname as _get_hostname
        current_hostname = _get_hostname()
        db = SessionLocal()
        try:
            from src.models.user import User
            user = db.query(User).filter(User.id == self.user_id).first()
            if user and user.settings:
                s = user.settings
                saved_hostname = s.get("hostname")
                if saved_hostname and saved_hostname != current_hostname:
                    self.theme_combo.setCurrentText("Светлая")
                    self.font_combo.setCurrentIndex(1)
                else:
                    theme = s.get("theme", "Светлая")
                    self.theme_combo.setCurrentText(theme)
                font_value = s.get("font_size", "Средний")
                if isinstance(font_value, int):
                    self.font_combo.setCurrentIndex({12: 0, 14: 1, 16: 2}.get(font_value, 1))
                else:
                    font_map = {"маленький": 0, "средний": 1, "большой": 2,
                                "12": 0, "14": 1, "16": 2,
                                "12px": 0, "14px": 1, "16px": 2}
                    self.font_combo.setCurrentIndex(
                        font_map.get(str(font_value).strip().lower(), 1)
                    )
                self.notif_check.setChecked(s.get("notifications", True))
                self.notif_goals_check.setChecked(s.get("notif_goals", True))
                self.notif_habits_check.setChecked(s.get("notif_habits", True))
                self.notif_focus_check.setChecked(s.get("notif_focus", True))
                self.quiet_check.setChecked(s.get("quiet_mode", False))
                qs = s.get("quiet_start", "22:00").split(":")
                qe = s.get("quiet_end", "08:00").split(":")
                self.quiet_start.setTime(QTime(int(qs[0]), int(qs[1])))
                self.quiet_end.setTime(QTime(int(qe[0]), int(qe[1])))
        except Exception:
            pass
        finally:
            db.close()

    def _save_settings(self):
        if not self.user_id:
            return
        from src.main import _hostname as _get_hostname
        font_values = {0: 12, 1: 14, 2: 16}
        theme = self.theme_combo.currentText()
        font_size = font_values.get(self.font_combo.currentIndex(), 14)
        s = {
            "theme": theme,
            "font_size": font_size,
            "hostname": _get_hostname(),
            "notifications": self.notif_check.isChecked(),
            "notif_goals": self.notif_goals_check.isChecked(),
            "notif_habits": self.notif_habits_check.isChecked(),
            "notif_focus": self.notif_focus_check.isChecked(),
            "quiet_mode": self.quiet_check.isChecked(),
            "quiet_start": self.quiet_start.time().toString("HH:mm"),
            "quiet_end": self.quiet_end.time().toString("HH:mm"),
        }
        db = SessionLocal()
        try:
            from src.models.user import User
            user = db.query(User).filter(User.id == self.user_id).first()
            if user:
                user.settings = s
                db.commit()
            QMessageBox.information(self, "Успех", "Настройки сохранены!")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()

    def _apply_theme(self):
        theme = self.theme_combo.currentText()
        font_sizes = {0: 12, 1: 14, 2: 16}
        font_size = font_sizes.get(self.font_combo.currentIndex(), 14)
        try:
            from src.main import apply_theme, save_user_theme
            apply_theme(theme, font_size)
            if self.user_id:
                save_user_theme(self.user_id, theme, font_size)
            QMessageBox.information(self, "Тема применена",
                                    f"Тема «{theme}» применена ко всему приложению.")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def _check_pwd_match(self):
        p1 = self.new_pwd.text()
        p2 = self.new_pwd2.text()
        from src.utils.validators import validate_password

        if not p1 and not p2:
            self.pwd_match_label.setText("")
            return
        if p1 and not validate_password(p1):
            self.pwd_match_label.setText(
                f"Пароль должен быть не менее {Settings().PASSWORD_MIN_LENGTH} символов, "
                "содержать буквы и цифры"
            )
            self.pwd_match_label.setStyleSheet("font-size:11px; color:#FF5252;")
            return
        if not p2:
            self.pwd_match_label.setText("")
            return
        if p1 == p2:
            self.pwd_match_label.setText("✓ Пароли совпадают")
            self.pwd_match_label.setStyleSheet("font-size:11px; color:#4CAF50;")
        else:
            self.pwd_match_label.setText("✗ Пароли не совпадают")
            self.pwd_match_label.setStyleSheet("font-size:11px; color:#FF5252;")

    def _change_password(self):
        old = self.old_pwd.text()
        new = self.new_pwd.text()
        new2 = self.new_pwd2.text()

        if not old or not new or not new2:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля пароля")
            return
        if new != new2:
            QMessageBox.warning(self, "Ошибка", "Новые пароли не совпадают")
            return
        from src.utils.validators import validate_password
        if not validate_password(new):
            QMessageBox.warning(self, "Ошибка",
                                "Пароль должен быть не менее 8 символов и содержать буквы и цифры")
            return

        db = SessionLocal()
        try:
            from src.services.auth_service import AuthService
            from src.models.user import User
            auth = AuthService(db)
            user = db.query(User).filter(User.id == self.user_id).first()
            if not user or not auth.verify_password(old, user.password_hash):
                QMessageBox.warning(self, "Ошибка", "Неверный текущий пароль")
                return
            auth.change_password(self.user_id, new)
            self.old_pwd.clear()
            self.new_pwd.clear()
            self.new_pwd2.clear()
            QMessageBox.information(self, "Успех", "Пароль успешно изменён!")
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()

    def _install_sys_notif(self):
        from src.services.system_notifications import NotificationInstaller
        ok = NotificationInstaller.install()
        if ok:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Успех",
                "Таймер уведомлений установлен!\n"
                "Уведомления будут приходить каждые 5 минут,\n"
                "даже когда приложение не запущено.")
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Ошибка",
                "Не удалось установить таймер.\n"
                "Убедитесь что systemd --user доступен.")
        self._refresh_sys_status()

    def _uninstall_sys_notif(self):
        from src.services.system_notifications import NotificationInstaller
        NotificationInstaller.uninstall()
        self._refresh_sys_status()

    def _refresh_sys_status(self):
        try:
            from src.services.system_notifications import NotificationInstaller
            if NotificationInstaller.is_installed():
                self.sys_status_lbl.setText("Таймер активен")
                self.sys_status_lbl.setStyleSheet("font-size:11px; color:#4CAF50;")
            else:
                self.sys_status_lbl.setText("Таймер не установлен")
                self.sys_status_lbl.setStyleSheet("font-size:11px; color:#888;")
        except Exception:
            pass

    def _request_deletion(self):
        reply = QMessageBox.question(
            self, "Удаление данных",
            "Все ваши данные будут удалены в течение 24 часов.\n"
            "Это действие необратимо.\n\nПродолжить?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        db = SessionLocal()
        try:
            from src.services.auth_service import AuthService
            AuthService(db).delete_user_data(self.user_id)
            QMessageBox.information(
                self, "Запрос принят",
                "Ваши данные будут удалены в течение 24 часов.\n"
                "Приложение будет закрыто."
            )
            import sys
            from PyQt5.QtWidgets import QApplication
            QApplication.instance().quit()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()
