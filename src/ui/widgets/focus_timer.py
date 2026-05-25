"""Таймер фокус-сессии с мониторингом процессов (ТЗ FR-009.1, FR-009.2)"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QMessageBox
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
from src.utils.process_monitor import ProcessMonitor


class FocusTimer(QWidget):
    timer_finished = pyqtSignal()
    timer_stopped  = pyqtSignal()

    def __init__(self, duration_minutes: int = 25, user_id: int = None,
                 block_level: int = 2, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)  # Всегда поверх
        self.setWindowModality(Qt.NonModal)
        self.duration_minutes  = duration_minutes
        self.user_id           = user_id
        self.block_level       = block_level   # 1=FULL, 2=NOTIFY, 3=NONE
        self.remaining_seconds = duration_minutes * 60
        self.total_seconds     = self.remaining_seconds
        self.is_running        = False
        self.session_id        = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._monitor_timer = QTimer(self)
        self._monitor_timer.timeout.connect(self._check_blocked_processes)
        self.monitor = ProcessMonitor()
        self._setup_ui()
        self._register_hotkeys()
        self._load_blocked_apps()

    def _load_blocked_apps(self):
        """Загрузить список заблокированных процессов из БД"""
        if not self.user_id:
            return
        try:
            from src.config.database import SessionLocal
            from src.repositories.blocked_app_repository import BlockedAppRepository
            db = SessionLocal()
            apps = BlockedAppRepository(db).get_by_user(self.user_id)
            self.monitor.set_blocked_apps({a.process_name: a.block_level_id for a in apps})
            db.close()
        except Exception:
            pass

    def _update_on_top(self, enabled: bool):
        """Включить режим поверх окон только при блокировке приложений из списка"""
        current = bool(self.windowFlags() & Qt.WindowStaysOnTopHint)
        if current == enabled:
            return
        self.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        self.show()
        if enabled:
            try:
                from src.main import supports_raise
                if supports_raise():
                    self.raise_()
                    self.activateWindow()
            except Exception:
                pass

    def _check_blocked_processes(self):
        """Проверять запущенные заблокированные процессы каждые 5 секунд"""
        if not self.is_running or self.block_level == 3:
            return
        blocked = self.monitor.check_blocked_running()
        self._update_on_top(bool(blocked) and self.block_level in (1, 2))
        for proc in blocked:
            app_level = proc.get("block_level_id", 2)
            if self.block_level == 1 and app_level == 1:
                self.monitor.terminate_process(proc["pid"], force=True)
                self._log(f"Принудительно завершён процесс: {proc['name']}")
            else:
                self._warn_blocked(proc["name"])

    def _warn_blocked(self, proc_name: str):
        """Показать уведомление о запуске заблокированного приложения"""
        QMessageBox.warning(
            self, "Нарушение фокуса",
            f"Запущено отвлекающее приложение: {proc_name}\n\nПожалуйста, закройте его для поддержания фокуса."
        )
        try:
            from src.services.notification_service import NotificationService
            from src.config.database import SessionLocal
            db = SessionLocal()
            svc = NotificationService(db)
            svc.send("Нарушение фокуса!",
                     f"Запущено отвлекающее приложение: {proc_name}")
            db.close()
        except Exception:
            pass

    def _log(self, message: str):
        try:
            from src.config.database import SessionLocal
            from src.models.system_log import SystemLog
            db = SessionLocal()
            db.add(SystemLog(event_type_id=3, message=message, context="focus_timer"))
            db.commit()
            db.close()
        except Exception:
            pass

    def _setup_ui(self):
        self.setWindowTitle("FocusGoal — Режим фокуса")
        self.setMinimumSize(480, 380)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Режим фокуса")
        title.setProperty("role", "dialogTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.time_label = QLabel(self._fmt(self.remaining_seconds))
        self.time_label.setProperty("role", "focusTimerTime")
        self.time_label.setProperty("state", "normal")
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)

        self.progress = QProgressBar()
        self.progress.setObjectName("focusTimerProgress")
        self.progress.setRange(0, self.total_seconds)
        self.progress.setValue(self.total_seconds)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(14)
        layout.addWidget(self.progress)

        self.info_label = QLabel(f"Сессия: {self.duration_minutes} мин")
        self.info_label.setProperty("role", "focusTimerInfo")
        self.info_label.setProperty("state", "normal")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(15)

        self.start_btn = QPushButton("Старт")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.setFixedSize(130, 50)
        self.start_btn.clicked.connect(self.start)

        self.pause_btn = QPushButton("Пауза")
        self.pause_btn.setObjectName("warningButton")
        self.pause_btn.setFixedSize(130, 50)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause)

        self.stop_btn = QPushButton("Завершить")
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.setFixedSize(130, 50)
        self.stop_btn.clicked.connect(self._stop)

        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.pause_btn)
        btn_row.addWidget(self.stop_btn)
        layout.addLayout(btn_row)

        hint = QLabel("Ctrl+Shift+Esc — экстренное завершение")
        hint.setProperty("role", "hintText")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

    def _register_hotkeys(self):
        sc = QShortcut(QKeySequence("Ctrl+Shift+Escape"), self)
        sc.activated.connect(self._emergency_stop)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._timer.start(1000)
            if self.block_level in (1, 2):
                self._monitor_timer.start(5000)
                self._check_blocked_processes()
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self._save_start()
            self._log(f"Фокус-сессия запущена: {self.duration_minutes} мин, уровень блокировки {self.block_level}")

    def pause(self):
        if self.is_running:
            self.is_running = False
            self._timer.stop()
            self._monitor_timer.stop()
            self.start_btn.setEnabled(True)
            self.start_btn.setText("Продолжить")
            self.pause_btn.setEnabled(False)

    def _stop(self):
        if QMessageBox.question(self, "Завершить?",
                                "Завершить фокус-сессию досрочно?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._finish(cancelled=True)

    def _emergency_stop(self):
        self._finish(cancelled=True)

    def _tick(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.time_label.setText(self._fmt(self.remaining_seconds))
            self.progress.setValue(self.remaining_seconds)
            if self.remaining_seconds == 300:
                self.info_label.setText("Осталось 5 минут!")
                self.info_label.setProperty("state", "warning")
                self.info_label.style().unpolish(self.info_label)
                self.info_label.style().polish(self.info_label)
        else:
            self._timer.stop()
            self.is_running = False
            self.time_label.setProperty("state", "finished")
            self.time_label.style().unpolish(self.time_label)
            self.time_label.style().polish(self.time_label)
            self._finish(cancelled=False)

    def _finish(self, cancelled: bool):
        self._timer.stop()
        self._monitor_timer.stop()
        self.is_running = False
        elapsed = (self.total_seconds - self.remaining_seconds) // 60
        self._save_stop(cancelled)
        self._log(f"Фокус-сессия завершена: {'отменена' if cancelled else 'успешно'}, время в фокусе {elapsed} мин")
        self.timer_stopped.emit()
        if not cancelled:
            self.timer_finished.emit()
            QMessageBox.information(self, "Молодец!",
                f"Сессия {self.duration_minutes} мин завершена успешно!")
        elif elapsed > 0:
            QMessageBox.information(self, "Сессия прервана",
                f"В фокусе: {elapsed} из {self.duration_minutes} мин.")
        self.close()

    def _save_start(self):
        if not self.user_id:
            return
        try:
            from src.config.database import SessionLocal
            from src.services.focus_service import FocusService
            db = SessionLocal()
            s = FocusService(db).start_session(self.user_id, self.duration_minutes)
            self.session_id = s.id
            db.close()
        except Exception:
            pass

    def _save_stop(self, cancelled: bool):
        if not self.session_id:
            return
        try:
            from src.config.database import SessionLocal
            from src.services.focus_service import FocusService
            db = SessionLocal()
            FocusService(db).stop_session(self.session_id, 2 if cancelled else 1)
            db.close()
        except Exception:
            pass

    @staticmethod
    def _fmt(s: int) -> str:
        return f"{s // 60:02d}:{s % 60:02d}"
