"""Диалог создания/редактирования цели (ТЗ FR-002.1, FR-002.3)"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QLabel,
    QComboBox, QDateEdit, QGroupBox, QScrollArea,
    QWidget, QCheckBox, QTimeEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QDate, QTime, QTimer
from datetime import datetime
from src.config.database import SessionLocal
from src.services.goal_service import GoalService


def _get_user_timezone(user_id: int | None) -> str:
    try:
        from src.config.database import SessionLocal
        from src.models.user import User
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first() if user_id else None
            return user.timezone if user and user.timezone else "Europe/Moscow"
        finally:
            db.close()
    except Exception:
        return "Europe/Moscow"


def _local_now(user_id: int | None = None) -> datetime:
    try:
        from zoneinfo import ZoneInfo
        tz = _get_user_timezone(user_id)
        return datetime.now(ZoneInfo(tz)).replace(tzinfo=None)
    except Exception:
        return datetime.now()


class CreateGoalDialog(QDialog):
    def __init__(self, user_id: int = None, parent=None, goal_id: int = None):
        super().__init__(parent)
        self.user_id = user_id
        self.goal_id = goal_id
        self.setWindowTitle("Редактировать цель" if goal_id else "Создать цель")
        self.setModal(True)
        self.setMinimumWidth(580)
        self.setMinimumHeight(680)
        self._setup_ui()
        if goal_id:
            QTimer.singleShot(50, self._load_goal)

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(14)
        layout.setContentsMargins(25, 25, 25, 25)

        title_lbl = QLabel("Редактировать цель" if self.goal_id else "Новая цель")
        title_lbl.setProperty("role", "accentTitle")
        title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)

        # Основное
        main_g = QGroupBox("Основная информация")
        ml = QFormLayout(main_g)
        ml.setSpacing(10)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название цели (обязательно, мин. 3 символа)")
        self.name_input.setMinimumHeight(42)
        ml.addRow("Название *:", self.name_input)
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Описание (необязательно)")
        self.desc_input.setMinimumHeight(90)
        self.desc_input.setMaximumHeight(130)
        ml.addRow("Описание:", self.desc_input)
        layout.addWidget(main_g)

        # Параметры
        param_g = QGroupBox("Параметры")
        pl = QFormLayout(param_g)
        pl.setSpacing(10)
        self.deadline_edit = QDateEdit()
        self.deadline_edit.setMinimumDate(QDate.currentDate().addDays(1))
        self.deadline_edit.setDate(QDate.currentDate().addDays(7))
        self.deadline_edit.setCalendarPopup(True)
        self.deadline_edit.setDisplayFormat("dd.MM.yyyy")
        self.deadline_edit.setMinimumHeight(42)
        pl.addRow("Срок выполнения:", self.deadline_edit)
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Высокий", "Средний", "Низкий"])
        self.priority_combo.setCurrentIndex(1)
        self.priority_combo.setMinimumHeight(42)
        pl.addRow("Приоритет:", self.priority_combo)
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems(["Разовая", "Ежедневная", "Еженедельная", "Ежемесячная"])
        self.repeat_combo.setMinimumHeight(42)
        pl.addRow("Повтор:", self.repeat_combo)
        self.fail_combo = QComboBox()
        self.fail_combo.addItems(["Перенести", "Отметить как пропущенную"])
        self.fail_combo.setCurrentIndex(1)
        self.fail_combo.setMinimumHeight(42)
        pl.addRow("При невыполнении:", self.fail_combo)
        layout.addWidget(param_g)

        # Напоминание
        rem_g = QGroupBox("Напоминание")
        rl = QFormLayout(rem_g)
        self.remind_check = QCheckBox("Добавить напоминание")
        rl.addRow(self.remind_check)
        self.remind_time = QTimeEdit()
        self.remind_time.setTime(QTime(9, 0))
        self.remind_time.setMinimumHeight(42)
        self.remind_time.setEnabled(False)
        rl.addRow("Время:", self.remind_time)
        self.remind_check.toggled.connect(self.remind_time.setEnabled)
        layout.addWidget(rem_g)

        layout.addStretch()

        # Кнопки
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("primaryButton")
        save_btn.setMinimumHeight(48)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumHeight(48)
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        container.setLayout(layout)
        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.addWidget(scroll)



    def _load_goal(self):
        db = SessionLocal()
        try:
            goals = GoalService(db).get_goals(self.user_id)
            goal = next((g for g in goals if g.id == self.goal_id), None)
            if not goal:
                return
            self.name_input.setText(goal.name)
            self.desc_input.setPlainText(goal.description or "")
            if goal.deadline:
                d = goal.deadline
                self.deadline_edit.setDate(QDate(d.year, d.month, d.day))
            pmap = {1: 0, 2: 1, 3: 2}
            self.priority_combo.setCurrentIndex(pmap.get(goal.priority_id, 1))
            rmap = {1: 0, 2: 1, 3: 2, 4: 3}
            self.repeat_combo.setCurrentIndex(rmap.get(goal.repeat_type_id, 0))
            fmap = {1: 0, 2: 1}
            self.fail_combo.setCurrentIndex(fmap.get(goal.fail_behavior_id, 1))
            # Сохранить оригинальное имя для корректного поиска напоминаний при обновлении
            self._original_name = goal.name
            # Попробовать загрузить существующее напоминание для этой цели
            try:
                from src.repositories.notification_repository import NotificationRepository
                notif_repo = NotificationRepository(db)
                notifs = notif_repo.get_by_user(self.user_id)
                for n in notifs:
                    if self._original_name and self._original_name in (n.content or ""):
                        if hasattr(n, 'send_at') and n.send_at:
                            self.remind_check.setChecked(True)
                            try:
                                t = n.send_at
                                self.remind_time.setTime(QTime(t.hour, t.minute))
                            except Exception:
                                pass
                        break
            except Exception:
                pass
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()

    def _save(self):
        name = self.name_input.text().strip()
        if len(name) < 3:
            QMessageBox.warning(self, "Ошибка", "Название должно быть минимум 3 символа")
            self.name_input.setProperty("validationState", "error")
            self.name_input.setFocus()
            return
        self.name_input.setProperty("validationState", "normal")

        desc = self.desc_input.toPlainText().strip()
        if desc and len(desc) < 4:
            QMessageBox.warning(self, "Ошибка", "Описание цели должно быть не менее 4 символов")
            self.desc_input.setFocus()
            return
        desc = desc or None
        qd = self.deadline_edit.date()
        deadline = datetime(qd.year(), qd.month(), qd.day())
        priority_id = {0: 1, 1: 2, 2: 3}.get(self.priority_combo.currentIndex(), 2)
        repeat_type_id = {0: 1, 1: 2, 2: 3, 3: 4}.get(self.repeat_combo.currentIndex(), 1)
        fail_behavior_id = {0: 1, 1: 2}.get(self.fail_combo.currentIndex(), 2)

        db = SessionLocal()
        try:
            svc = GoalService(db)
            data = dict(name=name, description=desc or None, deadline=deadline,
                        priority_id=priority_id, repeat_type_id=repeat_type_id,
                        fail_behavior_id=fail_behavior_id)
            if self.goal_id:
                svc.update_goal(self.goal_id, self.user_id, data)
                QMessageBox.information(self, "Успех", f"Цель «{name}» обновлена!")
                # Обновить/удалить напоминание: удалить старые напоминания с упоминанием предыдущего названия
                try:
                    from src.models.notification import NotificationSchedule
                    # удалить напоминания, которые содержат старое имя цели
                    if hasattr(self, '_original_name') and self._original_name:
                        db.query(NotificationSchedule).filter(
                            NotificationSchedule.user_id == self.user_id,
                            NotificationSchedule.content.ilike(f"%{self._original_name}%")
                        ).delete(synchronize_session=False)
                        db.commit()
                except Exception:
                    db.rollback()
                # Создать новое напоминание если отмечено
                if self.remind_check.isChecked():
                    try:
                        from src.models.notification import NotificationSchedule
                        from datetime import datetime as dt, timedelta
                        remind_time = self.remind_time.time()
                        reminder_dt = dt(
                            deadline.year,
                            deadline.month,
                            deadline.day,
                            remind_time.hour(),
                            remind_time.minute(),
                            0,
                        )
                        now = _local_now(self.user_id)
                        if reminder_dt <= now:
                            reminder_dt = now + timedelta(days=1)
                            reminder_dt = reminder_dt.replace(
                                hour=remind_time.hour(),
                                minute=remind_time.minute(),
                            )
                        notification = NotificationSchedule(
                            user_id=self.user_id,
                            type_id=1,
                            send_at=reminder_dt,
                            content=f"Напоминание: выполните цель «{name}»",
                            delivery_status_id=2
                        )
                        db.add(notification)
                        db.commit()
                    except Exception:
                        db.rollback()
            else:
                goal = svc.create_goal(self.user_id, data)
                QMessageBox.information(self, "Успех", f"Цель «{name}» создана!")
                
                # Создать напоминание если отмечена галочка
                if self.remind_check.isChecked():
                    from src.models.notification import NotificationSchedule
                    from datetime import datetime as dt, timedelta
                    
                    remind_time = self.remind_time.time()
                    qd = self.deadline_edit.date()
                    # Объединить дату дедлайна и время напоминания
                    reminder_dt = dt(
                        qd.year(), qd.month(), qd.day(),
                        remind_time.hour(), remind_time.minute(), 0,
                    )
                    
                    # Если время уже прошло, перенести на завтра
                    now = _local_now(self.user_id)
                    if reminder_dt <= now:
                        reminder_dt = now + timedelta(days=1)
                        reminder_dt = reminder_dt.replace(
                            hour=remind_time.hour(),
                            minute=remind_time.minute(),
                        )
                    
                    notification = NotificationSchedule(
                        user_id=self.user_id,
                        type_id=1,  # REMINDER
                        send_at=reminder_dt,
                        content=f"Напоминание: выполните цель «{name}»",
                        delivery_status_id=2  # PENDING
                    )
                    db.add(notification)
                    db.commit()
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()
