"""Диалог создания/редактирования привычки (ТЗ FR-003.1)"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QLabel,
    QComboBox, QGroupBox, QScrollArea, QWidget,
    QCheckBox, QTimeEdit, QSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt, QTime, QTimer
from datetime import date
from src.config.database import SessionLocal
from src.services.habit_service import HabitService


class CreateHabitDialog(QDialog):
    def __init__(self, user_id: int = None, parent=None, habit_id: int = None):
        super().__init__(parent)
        self.user_id = user_id
        self.habit_id = habit_id
        self.setWindowTitle("Редактировать привычку" if habit_id else "Создать привычку")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setMinimumHeight(640)
        self._setup_ui()
        if habit_id:
            QTimer.singleShot(50, self._load_habit)

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(14)
        layout.setContentsMargins(25, 25, 25, 25)

        title_lbl = QLabel(("Редактировать" if self.habit_id else "Новая привычка"))
        title_lbl.setProperty("role", "accentTitle")
        title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)

        # Основное
        main_g = QGroupBox("Основная информация")
        ml = QFormLayout(main_g)
        ml.setSpacing(10)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название привычки (мин. 3 символа)")
        self.name_input.setMinimumHeight(42)
        ml.addRow("Название *:", self.name_input)
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Описание (необязательно)")
        self.desc_input.setMinimumHeight(80)
        self.desc_input.setMaximumHeight(120)
        ml.addRow("Описание:", self.desc_input)
        layout.addWidget(main_g)

        # Параметры
        param_g = QGroupBox("Параметры")
        pl = QFormLayout(param_g)
        pl.setSpacing(10)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Ежедневная", "Еженедельная", "Ежемесячная"])
        self.type_combo.setMinimumHeight(42)
        pl.addRow("Частота:", self.type_combo)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Бинарная (факт выполнения)", "Количественная (счётчик)"])
        self.mode_combo.setMinimumHeight(42)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        pl.addRow("Режим:", self.mode_combo)
        self.target_spin = QSpinBox()
        self.target_spin.setRange(1, 9999)
        self.target_spin.setValue(1)
        self.target_spin.setMinimumHeight(42)
        self.target_spin.setEnabled(False)
        self.target_spin.setSuffix(" раз")
        pl.addRow("Целевое кол-во:", self.target_spin)
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

    def _on_mode_changed(self, idx: int):
        self.target_spin.setEnabled(idx == 1)


    def _load_habit(self):
        db = SessionLocal()
        try:
            habits = HabitService(db).get_habits(self.user_id)
            habit = next((h for h in habits if h.id == self.habit_id), None)
            if not habit:
                return
            self.name_input.setText(habit.name)
            self.desc_input.setPlainText(habit.description or "")
            tmap = {1: 0, 2: 1, 3: 2}
            self.type_combo.setCurrentIndex(tmap.get(habit.type_id, 0))
            mmap = {1: 0, 2: 1}
            self.mode_combo.setCurrentIndex(mmap.get(habit.mode_id, 0))
            if habit.target_value:
                self.target_spin.setValue(habit.target_value)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()

            # Попробовать загрузить существующее напоминание для этой привычки
            try:
                from src.repositories.notification_repository import NotificationRepository
                notif_repo = NotificationRepository(db)
                notifs = notif_repo.get_by_user(self.user_id)
                for n in notifs:
                    if habit.name and habit.name in (n.content or ""):
                        if hasattr(n, 'send_at') and n.send_at:
                            self.remind_check.setChecked(True)
                            try:
                                t = n.send_at
                                self.remind_time.setTime(QTime(t.hour, t.minute))
                            except Exception:
                                pass
                        break
+            # Сохранить оригинальное имя привычки для обновления напоминаний
+            try:
+                self._original_name = habit.name
+            except Exception:
+                self._original_name = None
            except Exception:
                pass

    def _save(self):
        name = self.name_input.text().strip()
        if len(name) < 3:
            QMessageBox.warning(self, "Ошибка", "Название должно быть минимум 3 символа")
            self.name_input.setProperty("validationState", "error")
            self.name_input.setFocus()
            return
        self.name_input.setProperty("validationState", "normal")

        desc = self.desc_input.toPlainText().strip() or None
        type_id = {0: 1, 1: 2, 2: 3}.get(self.type_combo.currentIndex(), 1)
        mode_id = {0: 1, 1: 2}.get(self.mode_combo.currentIndex(), 1)
        target = self.target_spin.value() if mode_id == 2 else None

        db = SessionLocal()
        try:
            svc = HabitService(db)
            data = dict(name=name, description=desc, type_id=type_id,
                        mode_id=mode_id, target_value=target, start_date=date.today())
            if self.habit_id:
                svc.update_habit(self.habit_id, self.user_id, data)
                QMessageBox.information(self, "Успех", f"Привычка «{name}» обновлена!")
                # Удалить старые напоминания, которые содержат старое имя привычки
                try:
                    from src.models.notification import NotificationSchedule
                    old_name = getattr(self, '_original_name', name)
                    db.query(NotificationSchedule).filter(
                        NotificationSchedule.user_id == self.user_id,
                        NotificationSchedule.content.ilike(f"%{old_name}%")
                    ).delete(synchronize_session=False)
                    db.commit()
                except Exception:
                    db.rollback()
                # Создать новое напоминание если отмечено
                if self.remind_check.isChecked():
                    try:
                        from src.models.notification import NotificationSchedule
                        from datetime import datetime as dt, timezone, timedelta
                        remind_time = self.remind_time.time()
                        now = dt.now(timezone.utc)
                        reminder_dt = now.replace(hour=remind_time.hour(), minute=remind_time.minute(), second=0, microsecond=0)
                        if reminder_dt <= now:
                            reminder_dt = reminder_dt + timedelta(days=1)
                        notification = NotificationSchedule(
                            user_id=self.user_id,
                            type_id=1,
                            send_at=reminder_dt,
                            content=f"Напоминание о привычке: {name}",
                            delivery_status_id=2
                        )
                        db.add(notification); db.commit()
                    except Exception:
                        db.rollback()
            else:
                svc.create_habit(self.user_id, data)
                QMessageBox.information(self, "Успех", f"Привычка «{name}» создана!")
                if self.remind_check.isChecked():
                    try:
                        from src.models.notification import NotificationSchedule
                        from datetime import datetime as dt, timezone, timedelta
                        remind_time = self.remind_time.time()
                        now = dt.now(timezone.utc)
                        reminder_dt = now.replace(hour=remind_time.hour(), minute=remind_time.minute(), second=0, microsecond=0)
                        if reminder_dt <= now:
                            reminder_dt = reminder_dt + timedelta(days=1)
                        notification = NotificationSchedule(
                            user_id=self.user_id,
                            type_id=1,
                            send_at=reminder_dt,
                            content=f"Напоминание о привычке: {name}",
                            delivery_status_id=2
                        )
                        db.add(notification); db.commit()
                    except Exception:
                        db.rollback()
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()
