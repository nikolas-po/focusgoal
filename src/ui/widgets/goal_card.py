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
        name_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
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
            deadline_lbl.setStyleSheet(f"font-size: 11px; color: {color};")
            layout.addWidget(deadline_lbl)

        layout.addStretch()

        # Кнопки
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        for icon, tip, signal, color in [
            ("✓", "Выполнена", self.goal_completed, "#4CAF50"),
            ("✎", "Редактировать", self.goal_edited, "#2196F3"),
            ("🗑", "Удалить", self.goal_deleted, "#FF5252"),
        ]:
            btn = QPushButton(icon)
            btn.setFixedSize(32, 32)
            btn.setToolTip(tip)
            btn.setStyleSheet(
                f"QPushButton {{ background: {color}; color: white; border: none; "
                f"border-radius: 16px; }}"
                f"QPushButton:hover {{ opacity: 0.85; }}"
            )
            btn.clicked.connect(lambda _, gid=self.goal_id, s=signal: s.emit(gid))
            btn_row.addWidget(btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        border = "#FF5252" if self.status == 3 else (
            "#4CAF50" if self.status == 2 else "#e0e0e0"
        )
        self.setStyleSheet(
            f"QFrame#goalCard {{ background: palette(base); border: 2px solid {border}; "
            f"border-radius: 10px; }}"
        )
