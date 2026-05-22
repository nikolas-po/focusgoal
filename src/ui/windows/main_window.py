"""Главное окно приложения (ТЗ FR-008)"""
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QAction, QStatusBar,
    QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from src.config.settings import Settings


class MainWindow(QMainWindow):
    def __init__(self, user_data: dict, parent=None):
        super().__init__(parent)
        self.user_id = user_data["id"]
        self.nickname = user_data["nickname"]
        self.settings = Settings()
        self.setWindowTitle(f"FocusGoal — {self.nickname}")
        self.setMinimumSize(1000, 680)
        self._loaded_tabs = set()  # индексы вкладок, для которых уже загружены данные
        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._setup_inactivity_timer()
        QTimer.singleShot(300, self.dashboard_tab.load_statistics)

    def _setup_ui(self):
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.currentChanged.connect(self._on_tab_activated)

        from src.ui.windows.dashboard_window import DashboardWindow
        self.dashboard_tab = DashboardWindow(self.user_id, self)
        self.tabs.addTab(self.dashboard_tab, "Главная")

        from src.ui.windows.goal_window import GoalWindow
        self.goal_tab = GoalWindow(self.user_id)
        self.tabs.addTab(self.goal_tab, "Цели")

        from src.ui.windows.habit_window import HabitWindow
        self.habit_tab = HabitWindow(self.user_id)
        self.tabs.addTab(self.habit_tab, "Привычки")

        from src.ui.windows.focus_window import FocusWindow
        self.focus_tab = FocusWindow(self.user_id)
        self.tabs.addTab(self.focus_tab, "Фокус")

        from src.ui.windows.statistics_window import StatisticsWindow
        self.stats_tab = StatisticsWindow(self.user_id)
        self.tabs.addTab(self.stats_tab, "Статистика")

        from src.ui.windows.blacklist_window import BlacklistWindow
        self.blacklist_tab = BlacklistWindow(self.user_id)
        self.tabs.addTab(self.blacklist_tab, "Чёрный список")

        from src.ui.windows.settings_window import SettingsWindow
        self.settings_tab = SettingsWindow(self.user_id)
        self.tabs.addTab(self.settings_tab, "Настройки")

        from src.ui.windows.backup_window import BackupWindow
        self.backup_tab = BackupWindow(self.user_id)
        self.tabs.addTab(self.backup_tab, "Резервные копии")

        self.setCentralWidget(self.tabs)

    def _on_tab_activated(self, index):
        """Загружаем данные для вкладки при первом переключении"""
        if index in self._loaded_tabs:
            return
        self._loaded_tabs.add(index)
        if index == 1:
            self.goal_tab.load_goals()
        elif index == 2:
            self.habit_tab._load_habits()
        elif index == 4:
            self.stats_tab._load_statistics()

    def _setup_menu(self):
        menu = self.menuBar()

        # Файл
        fm = menu.addMenu("Файл")
        for label, shortcut, slot in [
            ("Экспорт данных…", "Ctrl+S", self._open_export),
            ("Импорт данных…",  "Ctrl+I", self._open_import),
        ]:
            a = QAction(label, self)
            a.setShortcut(QKeySequence(shortcut))
            a.triggered.connect(slot)
            fm.addAction(a)
        fm.addSeparator()
        logout_a = QAction("Выйти из аккаунта", self)
        logout_a.setShortcut(QKeySequence("Ctrl+L"))
        logout_a.triggered.connect(self._logout)
        fm.addAction(logout_a)
        quit_a = QAction("Закрыть приложение", self)
        quit_a.setShortcut(QKeySequence("Ctrl+Q"))
        quit_a.triggered.connect(self._quit_app)
        fm.addAction(quit_a)

        # Цели
        gm = menu.addMenu("Цели")
        ng = QAction("Новая цель", self)
        ng.setShortcut(QKeySequence("Ctrl+N"))
        ng.triggered.connect(self._new_goal)
        gm.addAction(ng)

        # Привычки
        hm = menu.addMenu("Привычки")
        nh = QAction("Новая привычка", self)
        nh.setShortcut(QKeySequence("Ctrl+H"))
        nh.triggered.connect(self._new_habit)
        hm.addAction(nh)

        # Фокус
        focm = menu.addMenu("Фокус")
        sf = QAction("Запустить сессию", self)
        sf.setShortcut(QKeySequence("Ctrl+F"))
        sf.triggered.connect(lambda: self.tabs.setCurrentIndex(3))
        focm.addAction(sf)

        # Профиль
        prof_a = QAction("Мой профиль", self)
        prof_a.setShortcut(QKeySequence("Ctrl+P"))
        prof_a.triggered.connect(self._open_profile)
        menu.addAction(prof_a)

        # Напоминания
        rem_menu = menu.addMenu("Напоминания")
        rem_a = QAction("Управление напоминаниями", self)
        rem_a.triggered.connect(self._open_reminders)
        rem_menu.addAction(rem_a)

        # Помощь
        helpm = menu.addMenu("Помощь")
        about_a = QAction("О приложении", self)
        about_a.triggered.connect(self._show_about)
        helpm.addAction(about_a)

    def _setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"Добро пожаловать, {self.nickname}!")
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._refresh_status)
        self._status_timer.start(60_000)

    def _setup_inactivity_timer(self):
        self._inactivity_seconds = 0
        self._inactivity_limit = 15 * 60
        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.timeout.connect(self._check_inactivity)
        self._inactivity_timer.start(60_000)

    def _check_inactivity(self):
        self._inactivity_seconds += 60
        if self._inactivity_seconds >= self._inactivity_limit:
            self._lock_interface()

    def _lock_interface(self):
        self._inactivity_seconds = 0
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("Сессия заблокирована")
        dlg.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        dlg.setModal(True)
        dlg.setMinimumWidth(350)
        l = QVBoxLayout(dlg)
        l.addWidget(QLabel(
            "🔒 Сессия заблокирована из-за бездействия.\nВведите пароль для продолжения:"
        ))
        pwd = QLineEdit()
        pwd.setEchoMode(QLineEdit.Password)
        pwd.setMinimumHeight(40)
        l.addWidget(pwd)
        err = QLabel("")
        err.setStyleSheet("color: #FF5252;")
        l.addWidget(err)
        ok_btn = QPushButton("Разблокировать")
        ok_btn.setMinimumHeight(42)
        l.addWidget(ok_btn)

        def _try_unlock():
            from src.config.database import SessionLocal
            from src.services.auth_service import AuthService
            db = SessionLocal()
            try:
                AuthService(db).login(self.nickname, pwd.text())
                dlg.accept()
            except Exception:
                err.setText("Неверный пароль")
            finally:
                db.close()

        ok_btn.clicked.connect(_try_unlock)
        pwd.returnPressed.connect(_try_unlock)
        dlg.exec_()

    def start_focus_session(self, duration_minutes: int, block_level: int):
        from src.main import apply_theme, safe_raise
        from src.config import theme_state
        from src.ui.widgets.focus_timer import FocusTimer
        self._focus_timer = FocusTimer(
            duration_minutes=duration_minutes,
            user_id=self.user_id,
            block_level=block_level,
        )
        self._focus_timer.setWindowTitle(f"FocusGoal — Режим фокуса ({duration_minutes} мин)")
        self._focus_timer.show()
        apply_theme(theme_state.current_theme, theme_state.current_font_size)
        safe_raise(self._focus_timer)

    def mousePressEvent(self, e):
        self._inactivity_seconds = 0
        super().mousePressEvent(e)

    def keyPressEvent(self, e):
        self._inactivity_seconds = 0
        super().keyPressEvent(e)

    def _refresh_status(self):
        from datetime import datetime
        self.status_bar.showMessage(
            f"{self.nickname} | {datetime.now().strftime('%H:%M')} | FocusGoal v1.0"
        )

    def _new_goal(self):
        from src.ui.dialogs.create_goal_dialog import CreateGoalDialog
        if CreateGoalDialog(self.user_id, self).exec_():
            self.dashboard_tab.load_statistics()
            self.goal_tab.load_goals()

    def _new_habit(self):
        from src.ui.dialogs.create_habit_dialog import CreateHabitDialog
        if CreateHabitDialog(self.user_id, self).exec_():
            self.dashboard_tab.load_statistics()
            self.habit_tab._load_habits()

    def _open_export(self):
        from src.ui.dialogs.export_dialog import ExportDialog
        ExportDialog(self.user_id, self).exec_()

    def _open_import(self):
        from src.ui.dialogs.import_dialog import ImportDialog
        ImportDialog(self.user_id, self).exec_()

    def _open_profile(self):
        from src.main import safe_raise
        from src.ui.windows.profile_window import ProfileWindow
        if not hasattr(self, "_profile_win") or not self._profile_win.isVisible():
            self._profile_win = ProfileWindow(self.user_id, self.nickname)
            self._profile_win.setWindowTitle("Профиль — FocusGoal")
            self._profile_win.resize(800, 600)
        self._profile_win.show()
        safe_raise(self._profile_win)
        self._profile_win._load()

    def _open_reminders(self):
        from src.ui.windows.reminders_window import RemindersWindow
        if not hasattr(self, "_reminders_win") or not self._reminders_win.isVisible():
            self._reminders_win = RemindersWindow(self.user_id, self)
        self._reminders_win.show()
        self._reminders_win.raise_()

    def _logout(self):
        reply = QMessageBox.question(
            self, "Выход из аккаунта",
            "Выйти из аккаунта?\n\nЗапомненные данные будут очищены.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self._status_timer.stop()
        self._inactivity_timer.stop()

        from src.ui.windows.login_window import LoginWindow
        LoginWindow.clear_remembered(self.settings)

        self._login_win = LoginWindow(self.settings)
        self._login_win.show()

        self._skip_close_confirm = True
        self.close()

    def _quit_app(self):
        if QMessageBox.question(
            self, "Закрыть FocusGoal?", "Закрыть приложение?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self._stop_timers()
            for w in QApplication.instance().topLevelWidgets():
                if w != self:
                    w.close()
            self._skip_close_confirm = True
            self.close()

    def _show_about(self):
        QMessageBox.about(
            self, "О FocusGoal",
            "<b>FocusGoal v1.0.0</b><br><br>"
            "Система управления целями, привычками и фокус-сессиями.<br><br>"
            "© 2026 FocusGoal | Лицензия: Отсутсвует"
        )

    def _stop_timers(self):
        try:
            self._status_timer.stop()
        except Exception:
            pass
        try:
            self._inactivity_timer.stop()
        except Exception:
            pass

    def closeEvent(self, event):
        if getattr(self, "_skip_close_confirm", False):
            self._stop_timers()
            event.accept()
            return

        reply = QMessageBox.question(
            self, "Закрыть FocusGoal?", "Закрыть приложение?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._stop_timers()
            for w in QApplication.instance().topLevelWidgets():
                if w != self:
                    w.close()
            event.accept()
        else:
            event.ignore()