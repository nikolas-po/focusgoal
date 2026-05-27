"""Карточка привычки (ТЗ FR-003.2)"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QSizePolicy, QLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor


class HabitCard(QFrame):
    habit_completed = pyqtSignal(int)
    habit_edited    = pyqtSignal(int)
    habit_deleted   = pyqtSignal(int)
    habit_viewed    = pyqtSignal(int)

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
        name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        name_label.setProperty("role", "boldText")
        name_label.setWordWrap(True)
        title_row.addWidget(name_label, 1)

        status_dot = QLabel("🟢" if self.status == 1 else "⚪")
        title_row.addWidget(status_dot)
        layout.addLayout(title_row)

        # Тип
        type_map = {1: "Ежедневная", 2: "Еженедельная", 3: "🗓 Ежемесячная"}
        type_label = QLabel(type_map.get(self.habit_type, ""))
        type_label.setProperty("role", "mutedSmallText")
        layout.addWidget(type_label)

        # Серия
        streak_label = QLabel(f"Серия: {self.streak} дн.")
        streak_label.setProperty("role", "warningText")
        layout.addWidget(streak_label)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("habitProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(self.progress)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat(f"{self.progress}%")
        self.progress_bar.setFixedHeight(14)
        layout.addWidget(self.progress_bar)

        # Кнопки
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSizeConstraint(QLayout.SetMinimumSize)
        btn_row.addStretch(1)

        done_btn = QPushButton("✓")
        done_btn.setObjectName("circlePrimaryButton")
        done_btn.setFixedSize(36, 36)
        done_btn.setToolTip("Отметить выполненной")
        done_btn.setEnabled(self.status == 1)
        done_btn.clicked.connect(lambda: self.habit_completed.emit(self.habit_id))
        done_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        edit_btn = QPushButton("✎")
        edit_btn.setObjectName("circleSecondaryButton")
        edit_btn.setFixedSize(36, 36)
        edit_btn.setToolTip("Редактировать")
        edit_btn.clicked.connect(lambda: self.habit_edited.emit(self.habit_id))
        edit_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        del_btn = QPushButton("🗑")
        del_btn.setObjectName("dangerCircleButton")
        del_btn.setFixedSize(36, 36)
        del_btn.setToolTip("Удалить")
        del_btn.clicked.connect(lambda: self.habit_deleted.emit(self.habit_id))
        del_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        view_btn = QPushButton("👁")
        view_btn.setObjectName("circleSecondaryButton")
        view_btn.setFixedSize(36, 36)
        view_btn.setToolTip("Просмотр")
        view_btn.clicked.connect(lambda: self.habit_viewed.emit(self.habit_id))
        view_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        btn_row.addWidget(done_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(view_btn)
        btn_row.addWidget(del_btn)
        layout.addLayout(btn_row)

    def _apply_style(self):
        self.setProperty("positiveStreak", self.streak > 0)
