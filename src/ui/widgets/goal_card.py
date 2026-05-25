"""Карточка цели"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from src.utils.date_utils import days_until, is_overdue


class GoalCard(QFrame):
    goal_completed = pyqtSignal(int)
    goal_edited    = pyqtSignal(int)
    goal_deleted   = pyqtSignal(int)

    def __init__(self, goal_data: dict, parent=None):
        super().__init__(parent)
        self.goal_id   = goal_data.get("id")
        self.name      = goal_data.get("name", "")
        self.priority  = goal_data.get("priority_id", 2)
        self.status    = goal_data.get("status_id", 1)
        self.deadline  = goal_data.get("deadline")
        self._setup_ui()

    def _setup_ui(self):
        self.setMinimumSize(240, 140)
        self.setMaximumWidth(380)
        self.setObjectName("goalCard")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(14, 14, 14, 14)

        # Название + приоритет
        header = QHBoxLayout()
        prio_icons = {1: "🔴", 2: "🟡", 3: "🟢"}
        prio = QLabel(prio_icons.get(self.priority, "🟡"))
        header.addWidget(prio)
        name_lbl = QLabel(self.name[:35])
        name_lbl.setProperty("role", "boldSmallText")
        name_lbl.setWordWrap(True)
        header.addWidget(name_lbl, 1)
        layout.addLayout(header)

        # Срок
        if self.deadline:
            d = self.deadline
            if hasattr(d, "date"):
                d = d.date()
            overdue = is_overdue(d)
            days = days_until(d)
            if overdue:
                color, text = "#FF5252", f"Просрочено на {abs(days)} дн."
            elif days == 0:
                color, text = "#FF9800", "Сегодня!"
            else:
                color, text = "#4CAF50", f"Осталось {days} дн."
            deadline_lbl = QLabel(text)
            deadline_lbl.setProperty("deadlineStatus", "overdue" if overdue else "today" if days == 0 else "normal")
            layout.addWidget(deadline_lbl)

        layout.addStretch()

        # Кнопки
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        for icon, tip, signal, name in [
            ("✓", "Выполнена", self.goal_completed, "circlePrimaryButton"),
            ("✎", "Редактировать", self.goal_edited, "circleSecondaryButton"),
            ("🗑", "Удалить", self.goal_deleted, "dangerCircleButton"),
        ]:
            btn = QPushButton(icon)
            btn.setObjectName(name)
            btn.setFixedSize(32, 32)
            btn.setToolTip(tip)
            btn.clicked.connect(lambda _, gid=self.goal_id, s=signal: s.emit(gid))
            btn_row.addWidget(btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.setProperty("statusBorder", self.status)
