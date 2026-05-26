"""Окно фокус-режима (ТЗ FR-009)"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QRadioButton, QButtonGroup,
    QSpinBox, QCheckBox, QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt


class FocusWindow(QWidget):
    def __init__(self, user_id: int = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self._timer_widget = None
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Режим фокуса")
        title.setProperty("role", "valueLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("Заблокируйте отвлекающие приложения и сосредоточьтесь на важном.")
        desc.setProperty("role", "smallText")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        # Длительность
        dur_group = QGroupBox("Длительность сессии")
        dur_layout = QVBoxLayout(dur_group)
        self.dur_group = QButtonGroup()
        for mins, label in [
            (25, "25 мин — Классическая сессия"),
            (50, "50 мин — Длинная сессия"),
            (90, "90 мин — Глубокая работа"),
        ]:
            rb = QRadioButton(label)
            self.dur_group.addButton(rb, mins)
            dur_layout.addWidget(rb)
            if mins == 25:
                rb.setChecked(True)

        custom_row = QHBoxLayout()
        custom_rb = QRadioButton("Свой вариант:")
        self.dur_group.addButton(custom_rb, 0)
        self.custom_spin = QSpinBox()
        self.custom_spin.setRange(5, 480)
        self.custom_spin.setValue(30)
        self.custom_spin.setSuffix(" мин")
        self.custom_spin.setMinimumHeight(36)
        self.custom_spin.setEnabled(False)
        custom_rb.toggled.connect(self.custom_spin.setEnabled)
        custom_row.addWidget(custom_rb)
        custom_row.addWidget(self.custom_spin)
        custom_row.addStretch()
        dur_layout.addLayout(custom_row)
        layout.addWidget(dur_group)

        # Уровень блокировки
        block_group = QGroupBox("Уровень блокировки")
        block_layout = QVBoxLayout(block_group)
        self.block_grp = QButtonGroup()
        for bid, label in [
            (1, "Строгий — принудительное завершение процессов (требует прав root/admin)"),
            (2, "Мягкий — уведомление при открытии отвлекающих приложений"),
            (3, "Без блокировки — только таймер"),
        ]:
            rb = QRadioButton(label)
            self.block_grp.addButton(rb, bid)
            block_layout.addWidget(rb)
            if bid == 2:
                rb.setChecked(True)
        layout.addWidget(block_group)

        tip = QLabel(
            "Ctrl+Shift+Esc — экстренное завершение сессии\n"
            "Для строгой блокировки  приложение потребует права администратора и будет перезапущено с этими правами. Если вы не предоставите права, сессия не запустится."
        )
        tip.setProperty("role", "tipText")
        tip.setWordWrap(True)
        layout.addWidget(tip)

        layout.addSpacing(10)
        start_btn = QPushButton("Запустить фокус-сессию")
        start_btn.setObjectName("focusStartBtn")
        start_btn.setMinimumHeight(58)
        start_btn.clicked.connect(self._start)
        layout.addWidget(start_btn)

        container.setLayout(layout)
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def _get_duration(self) -> int:
        bid = self.dur_group.checkedId()
        return self.custom_spin.value() if bid == 0 else bid

    def _start(self):
        duration = self._get_duration()
        block_level = self.block_grp.checkedId()

        if block_level == 1:
            from src.utils.process_monitor import ProcessMonitor
            pm = ProcessMonitor()
            if not pm.check_admin_rights():
                reply = QMessageBox.question(
                    self, "Требуются права администратора",
                    "Для строгой блокировки нужны права администратора.\n\n"
                    "Запустить приложение с правами администратора?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    launch_args = [
                        f"--resume-user={self.user_id}",
                        "--resume-focus",
                        f"--resume-duration={duration}",
                        f"--resume-block-level={block_level}",
                    ]
                    if pm.request_admin_rights(launch_args=launch_args):
                        QMessageBox.information(
                            self, "Перезапуск",
                            "Приложение перезапускается с правами администратора."
                        )
                        from PyQt5.QtWidgets import QApplication
                        QApplication.instance().quit()
                        return
                    QMessageBox.warning(self, "Ошибка", "Не удалось получить права администратора.")
                return

        if self._timer_widget and self._timer_widget.isVisible():
            self._timer_widget.close()

        from src.ui.widgets.focus_timer import FocusTimer
        from src.main import apply_theme, safe_raise
        from src.config import theme_state 

        self._timer_widget = FocusTimer(
            duration_minutes=duration,
            user_id=self.user_id,
            block_level=block_level,
        )
        self._timer_widget.setWindowTitle(f"FocusGoal — Сессия {duration} мин")
        self._timer_widget.show()
        # Применяем тему из единственного источника правды
        apply_theme(theme_state.current_theme, theme_state.current_font_size)
        safe_raise(self._timer_widget)
