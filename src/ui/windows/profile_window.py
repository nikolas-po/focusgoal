"""Профиль пользователя и журнал событий (ТЗ FR-008, Ctrl+P)"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QTableWidget,
    QTableWidgetItem, QGroupBox, QFormLayout,
    QScrollArea, QFrame, QHeaderView, QLineEdit,
    QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt
from src.config.database import SessionLocal
from src.config.constants import GOAL_STATUS_NAMES, HABIT_STATUS_NAMES


class ProfileWindow(QWidget):
    def __init__(self, user_id: int = None, nickname: str = "",  parent=None):
        super().__init__(parent)
        self.user_id  = user_id
        self.nickname = nickname
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # Шапка профиля
        header = QHBoxLayout()
        avatar = QLabel("👤")
        avatar.setProperty("role", "xxLargeIcon")
        header.addWidget(avatar)
        info = QVBoxLayout()
        self.name_lbl = QLabel(self.nickname)
        self.name_lbl.setProperty("role", "pageTitle")
        info.addWidget(self.name_lbl)
        self.reg_lbl = QLabel("")
        self.reg_lbl.setProperty("role", "mutedText")
        info.addWidget(self.reg_lbl)
        self.email_lbl = QLabel("")
        self.email_lbl.setProperty("role", "smallText")
        info.addWidget(self.email_lbl)
        header.addLayout(info)
        header.addStretch()
        layout.addLayout(header)

        # Вкладки
        tabs = QTabWidget()

        #Статистика профиля
        stat_tab = QWidget()
        sl = QVBoxLayout(stat_tab)
        sl.setContentsMargins(10, 10, 10, 10)
        grid = QHBoxLayout()
        self.stat_cards = {}
        for key, label in [
            ("goals",    "Целей создано"),
            ("habits",   "Привычек"),
            ("sessions", "Фокус-сессий"),
            ("streak",   "Макс. серия"),
        ]:
            card = self._make_card(label, "—")
            self.stat_cards[key] = card
            grid.addWidget(card)
        sl.addLayout(grid)
        sl.addStretch()
        tabs.addTab(stat_tab, "Статистика")

        # Журнал событий 
        log_tab = QWidget()
        ll = QVBoxLayout(log_tab)
        ll.setContentsMargins(10, 10, 10, 10)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Тип:"))
        self.log_type_combo = QComboBox()
        self.log_type_combo.addItems(["Все", "Ошибки", "Предупреждения", "Информация"])
        self.log_type_combo.setMinimumHeight(34)
        self.log_type_combo.currentIndexChanged.connect(self._load_logs)
        filter_row.addWidget(self.log_type_combo)
        filter_row.addStretch()
        clear_btn = QPushButton("🗑 Очистить лог")
        clear_btn.setMinimumHeight(34)
        clear_btn.clicked.connect(self._clear_log)
        filter_row.addWidget(clear_btn)
        ll.addLayout(filter_row)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(
            ["Дата/Время", "Тип", "Контекст", "Сообщение"]
        )
        self.log_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setColumnWidth(0, 140)
        self.log_table.setColumnWidth(1, 100)
        self.log_table.setColumnWidth(2, 130)
        self.log_table.setWordWrap(True)
        ll.addWidget(self.log_table)
        tabs.addTab(log_tab, "Журнал событий")

        settings_tab = QWidget()
        sl = QVBoxLayout(settings_tab)
        sl.setContentsMargins(10, 10, 10, 10)
        settings_g = QGroupBox("Часовой пояс")
        fl = QFormLayout(settings_g)
        self.tz_combo = QComboBox()
        self.tz_combo.addItems([
            "Europe/Moscow", "Europe/London", "Europe/Paris", "Europe/Berlin",
            "America/New_York", "America/Los_Angeles", "Asia/Tokyo", "Asia/Shanghai",
            "Australia/Sydney", "UTC"
        ])
        self.tz_combo.setMinimumHeight(38)
        fl.addRow("Часовой пояс:", self.tz_combo)
        save_tz_btn = QPushButton("Сохранить")
        save_tz_btn.setMinimumHeight(44)
        save_tz_btn.clicked.connect(self._save_timezone)
        fl.addRow("", save_tz_btn)
        sl.addWidget(settings_g)
        sl.addStretch()
        tabs.addTab(settings_tab, "Настройки")

        layout.addWidget(tabs)

    def _make_card(self, title: str, value: str) -> QFrame:
        f = QFrame()
        f.setObjectName("profileCard")
        f.setObjectName("profileCard")
        cl = QVBoxLayout(f)
        cl.setContentsMargins(12, 10, 12, 10)
        tl = QLabel(title)
        tl.setProperty("role", "mutedText")
        cl.addWidget(tl)
        vl = QLabel(value)
        vl.setObjectName("val")
        vl.setProperty("role", "pageTitle")
        cl.addWidget(vl)
        return f

    def _set_card(self, card: QFrame, value: str):
        for lbl in card.findChildren(QLabel):
            if lbl.objectName() == "val":
                lbl.setText(value)

    def _load(self):
        db = SessionLocal()
        try:
            from src.models.user import User
            from src.models.goal import Goal
            from src.models.habit import Habit
            from src.models.focus_session import FocusSession
            from sqlalchemy import func

            user = db.query(User).filter(User.id == self.user_id).first()
            if user:
                self.reg_lbl.setText(f"Зарегистрирован: {user.registered_at.strftime('%d.%m.%Y')}")
                self.email_lbl.setText(f"Email: {user.email or 'не указан'}")
                idx = self.tz_combo.findText(user.timezone or "Europe/Moscow")
                if idx >= 0:
                    self.tz_combo.setCurrentIndex(idx)

            goals_cnt    = db.query(func.count(Goal.id)).filter(Goal.user_id == self.user_id).scalar() or 0
            habits_cnt   = db.query(func.count(Habit.id)).filter(Habit.user_id == self.user_id).scalar() or 0
            sessions_cnt = db.query(func.count(FocusSession.id)).filter(FocusSession.user_id == self.user_id).scalar() or 0
            max_streak   = db.query(func.max(Habit.max_streak)).filter(Habit.user_id == self.user_id).scalar() or 0

            self._set_card(self.stat_cards["goals"],    str(goals_cnt))
            self._set_card(self.stat_cards["habits"],   str(habits_cnt))
            self._set_card(self.stat_cards["sessions"], str(sessions_cnt))
            self._set_card(self.stat_cards["streak"],   f"{max_streak} дн.")
        except Exception:
            pass
        finally:
            db.close()
        self._load_logs()

    def _load_logs(self):
        self.log_table.setRowCount(0)
        db = SessionLocal()
        try:
            from src.models.system_log import SystemLog
            type_filter = self.log_type_combo.currentIndex()
            q = db.query(SystemLog)
            if type_filter == 1: q = q.filter(SystemLog.event_type_id == 1)
            elif type_filter == 2: q = q.filter(SystemLog.event_type_id == 2)
            elif type_filter == 3: q = q.filter(SystemLog.event_type_id == 3)
            logs = q.order_by(SystemLog.event_at.desc()).limit(200).all()

            type_labels = {1: "Ошибка", 2: "Предупр.", 3: "ℹИнфо"}
            self.log_table.setRowCount(len(logs))
            for i, log in enumerate(logs):
                self.log_table.setItem(i, 0, QTableWidgetItem(
                    log.event_at.strftime("%d.%m.%Y %H:%M:%S") if log.event_at else ""))
                self.log_table.setItem(i, 1, QTableWidgetItem(
                    type_labels.get(log.event_type_id, "Инфо")))
                item_ctx = QTableWidgetItem(log.context or "")
                item_msg = QTableWidgetItem(log.message or "")
                item_ctx.setFlags(item_ctx.flags() & ~Qt.ItemIsEditable)
                item_msg.setFlags(item_msg.flags() & ~Qt.ItemIsEditable)
                self.log_table.setItem(i, 2, item_ctx)
                self.log_table.setItem(i, 3, item_msg)
            try:
                self.log_table.resizeRowsToContents()
            except Exception:
                pass
        except Exception as e:
            pass
        finally:
            db.close()

    def _clear_log(self):
        if QMessageBox.question(self, "Очистить журнал?",
                                "Удалить все записи системного журнала?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        db = SessionLocal()
        try:
            from src.models.system_log import SystemLog
            db.query(SystemLog).delete()
            db.commit()
            self._load_logs()
            QMessageBox.information(self, "Готово", "Журнал очищен")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()

    def _save_timezone(self):
        db = SessionLocal()
        try:
            from src.models.user import User
            user = db.query(User).filter(User.id == self.user_id).first()
            if user:
                user.timezone = self.tz_combo.currentText()
                db.commit()
                QMessageBox.information(self, "Готово", f"Часовой пояс изменён на {user.timezone}")
            else:
                QMessageBox.warning(self, "Ошибка", "Пользователь не найден")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()
