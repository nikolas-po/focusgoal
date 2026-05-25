"""Окно управления напоминаниями"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt
from src.config.database import SessionLocal
from src.models.notification import NotificationSchedule
from src.services.notification_service import NotificationService


class RemindersWindow(QWidget):
    def __init__(self, user_id: int = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Напоминания — FocusGoal")
        self.setMinimumSize(700, 400)
        self._setup_ui()
        self._load_reminders()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Мои напоминания")
        title.setProperty("role", "dialogTitle")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Тип", "Объект", "Время отправки", "Действия"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self._load_reminders)
        btn_row.addWidget(refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _load_reminders(self):
        self.table.setRowCount(0)
        db = SessionLocal()
        try:
            reminders = db.query(NotificationSchedule).filter(
                NotificationSchedule.user_id == self.user_id,
                NotificationSchedule.delivery_status_id == 2
            ).all()
            self.table.setRowCount(len(reminders))
            for i, r in enumerate(reminders):
                self.table.setItem(i, 0, QTableWidgetItem(str(r.id)))
                obj_type = "Цель" if r.content.startswith("goal_") else "Привычка"
                self.table.setItem(i, 1, QTableWidgetItem(obj_type))
                obj_name = self._get_object_name(db, r.content)
                self.table.setItem(i, 2, QTableWidgetItem(obj_name))
                self.table.setItem(i, 3, QTableWidgetItem(r.send_at.strftime("%d.%m.%Y %H:%M")))
                del_btn = QPushButton("Удалить")
                del_btn.setFixedSize(80, 30)
                del_btn.clicked.connect(lambda _, rid=r.id: self._delete_reminder(rid))
                self.table.setCellWidget(i, 4, del_btn)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()

    def _get_object_name(self, db, content: str) -> str:
        from src.models.goal import Goal
        from src.models.habit import Habit
        if content.startswith("goal_"):
            gid = int(content.split("_")[1])
            goal = db.query(Goal).filter(Goal.id == gid).first()
            return goal.name if goal else "[удалено]"
        elif content.startswith("habit_"):
            hid = int(content.split("_")[1])
            habit = db.query(Habit).filter(Habit.id == hid).first()
            return habit.name if habit else "[удалено]"
        return content

    def _delete_reminder(self, reminder_id: int):
        if QMessageBox.question(self, "Удалить напоминание?",
                                "Удалить это напоминание?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        db = SessionLocal()
        try:
            reminder = db.query(NotificationSchedule).filter(NotificationSchedule.id == reminder_id).first()
            if reminder:
                job_id = reminder.content
                db.delete(reminder)
                db.commit()
                notif = NotificationService(db, self.user_id)
                notif.remove_reminder(job_id)
            self._load_reminders()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()