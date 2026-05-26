"""Диалог просмотра деталей цели (ТЗ FR-002.2)"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QGroupBox, QScrollArea,
    QWidget, QMessageBox
)
from PyQt5.QtCore import Qt
from src.config.database import SessionLocal
from src.services.goal_service import GoalService
from src.config.constants import (
    GOAL_STATUS_NAMES, GOAL_PRIORITY_NAMES,
    REPEAT_TYPE_NAMES, FAIL_BEHAVIOR_NAMES
)
from src.repositories.notification_repository import NotificationRepository


class GoalDetailDialog(QDialog):
    def __init__(self, goal_data: dict, user_id: int = None, parent=None):
        super().__init__(parent)
        self.goal_data = goal_data
        self.user_id = user_id
        self.setWindowTitle("Детали цели")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel(f"🎯 {self.goal_data.get('name', '')}")
        title.setProperty("role", "sectionTitle")
        title.setWordWrap(True)
        layout.addWidget(title)

        info_g = QGroupBox("Подробная информация")
        form = QFormLayout(info_g)
        form.setSpacing(8)

        desc = self.goal_data.get("description") or "—"
        form.addRow("Описание:", QLabel(desc))

        deadline = self.goal_data.get("deadline")
        if deadline:
            if hasattr(deadline, "strftime"):
                deadline_str = deadline.strftime("%d.%m.%Y")
            else:
                deadline_str = str(deadline)
        else:
            deadline_str = "—"
        form.addRow("Срок:", QLabel(deadline_str))

        prio = GOAL_PRIORITY_NAMES.get(self.goal_data.get("priority_id", 2), "Средний")
        form.addRow("Приоритет:", QLabel(prio))

        status = GOAL_STATUS_NAMES.get(self.goal_data.get("status_id", 1), "Активна")
        form.addRow("Статус:", QLabel(status))

        repeat = REPEAT_TYPE_NAMES.get(self.goal_data.get("repeat_type_id", 1), "Разовая")
        form.addRow("Повтор:", QLabel(repeat))

        fail = FAIL_BEHAVIOR_NAMES.get(self.goal_data.get("fail_behavior_id", 2), "Пропустить")
        form.addRow("При невыполнении:", QLabel(fail))

        created = self.goal_data.get("created_at")
        if created and hasattr(created, "strftime"):
            form.addRow("Создана:", QLabel(created.strftime("%d.%m.%Y")))

        layout.addWidget(info_g)
        # Показать напоминания, связанные с этой целью
        try:
            db2 = SessionLocal()
            notif_repo = NotificationRepository(db2)
            notifs_all = notif_repo.get_by_user(self.user_id) if self.user_id else []
            related = [n for n in notifs_all if self.goal_data.get('name') and self.goal_data.get('name') in (n.content or "")]
            if related:
                rem_g = QGroupBox("Напоминания")
                rl = QVBoxLayout(rem_g)
                for n in related:
                    s = n.send_at
                    rl.addWidget(QLabel(f"{s}: {n.content} ({'Отправлено' if n.delivery_status_id==3 else 'Ожидает'})"))
                layout.addWidget(rem_g)
            db2.close()
        except Exception:
            pass
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        complete_btn = QPushButton("Отметить выполненной")
        complete_btn.setMinimumHeight(44)
        complete_btn.setObjectName("primaryButton")
        complete_btn.clicked.connect(self._complete)
        btn_row.addWidget(complete_btn)
        edit_btn = QPushButton("✎ Редактировать")
        edit_btn.setMinimumHeight(44)
        edit_btn.setObjectName("secondaryButton")
        edit_btn.clicked.connect(self._edit)
        btn_row.addWidget(edit_btn)
        close_btn = QPushButton("Закрыть")
        close_btn.setMinimumHeight(44)
        close_btn.setObjectName("cancelButton")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _complete(self):
        goal_id = self.goal_data.get("id")
        if not goal_id or not self.user_id:
            return
        db = SessionLocal()
        try:
            GoalService(db).complete_goal(goal_id, self.user_id)
            QMessageBox.information(self, "Успех", "Цель выполнена! 🎉")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()

    def _edit(self):
        goal_id = self.goal_data.get("id")
        if not goal_id:
            return
        from src.ui.dialogs.create_goal_dialog import CreateGoalDialog
        dialog = CreateGoalDialog(self.user_id, self, goal_id=goal_id)
        if dialog.exec_():
            self.accept()
