"""Карточка привычки (ТЗ FR-003.2)"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor


class HabitCard(QFrame):
    habit_completed = pyqtSignal(int)
    habit_edited    = pyqtSignal(int)
    habit_deleted   = pyqtSignal(int)

    def __init__(self, habit_data: dict, parent=None):
        super().__init__(parent)
        self.habit_id   = habit_data.get("id")
        self.habit_name = habit_data.get("name", "")
        self.streak     = habit_data.get("streak", 0)
        self.progress   = habit_data.get("progress", 0)
        self.status     = habit_data.get("status", 1)
        self.habit_type = habit_data.get("type", 1)
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        self.setMinimumSize(240, 200)
        self.setMaximumWidth(360)
        self.setObjectName("habitCard")
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(14, 14, 14, 14)

        # Заголовок + статус
        title_row = QHBoxLayout()
        name_label = QLabel(self.habit_name[:30])
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        name_label.setWordWrap(True)
        title_row.addWidget(name_label, 1)

        status_dot = QLabel("🟢" if self.status == 1 else "⚪")
        title_row.addWidget(status_dot)
        layout.addLayout(title_row)

        # Тип
        type_map = {1: "Ежедневная", 2: "Еженедельная", 3: "Ежемесячная"}
        type_label = QLabel(type_map.get(self.habit_type, ""))
        type_label.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(type_label)

        # Серия
        streak_label = QLabel(f"Серия: {self.streak} дн.")
        streak_label.setStyleSheet("font-size: 12px; color: #FF6F00; font-weight: bold;")
        layout.addWidget(streak_label)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(self.progress)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat(f"{self.progress}%")
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 1px solid #ccc; border-radius: 7px; "
            "background: #e0e0e0; text-align: center; font-size: 10px; }"
            "QProgressBar::chunk { background: #4CAF50; border-radius: 6px; }"
        )
        layout.addWidget(self.progress_bar)

        # Кнопки
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        done_btn = QPushButton("✓")
        done_btn.setFixedSize(36, 36)
        done_btn.setToolTip("Отметить выполненной")
        done_btn.setEnabled(self.status == 1)
        done_btn.setStyleSheet(
            "QPushButton { background: #4CAF50; color: white; border: none; "
            "border-radius: 18px; font-size: 16px; font-weight: bold; padding: 0px; }"
            "QPushButton:hover { background: #45a049; }"
            "QPushButton:disabled { background: #cccccc; }"
        )
        done_btn.clicked.connect(lambda: self.habit_completed.emit(self.habit_id))

        edit_btn = QPushButton("✎")
        edit_btn.setFixedSize(36, 36)
        edit_btn.setToolTip("Редактировать")
        edit_btn.setStyleSheet(
            "QPushButton { background: #2196F3; color: white; border: none; "
            "border-radius: 18px; font-size: 16px; padding: 0px; }"
            "QPushButton:hover { background: #1976D2; }"
        )
        edit_btn.clicked.connect(lambda: self.habit_edited.emit(self.habit_id))

        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(36, 36)
        del_btn.setToolTip("Удалить")
        del_btn.setStyleSheet(
            "QPushButton { background: #FF5252; color: white; border: none; "
            "border-radius: 18px; font-size: 16px; padding: 0px; }"
            "QPushButton:hover { background: #E53935; }"
        )
        del_btn.clicked.connect(lambda: self.habit_deleted.emit(self.habit_id))

        btn_row.addWidget(done_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _apply_style(self):
        border = "#4CAF50" if self.streak > 0 else "#e0e0e0"
        self.setStyleSheet(
            f"QFrame#habitCard {{ background: palette(base); border: 2px solid {border}; "
            f"border-radius: 10px; }}"
        )
