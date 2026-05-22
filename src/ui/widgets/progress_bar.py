"""Кастомный прогресс-бар с меткой"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout
from PyQt5.QtCore import Qt


class LabeledProgressBar(QWidget):
    def __init__(self, label: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)

        top_row = QHBoxLayout()
        self.label = QLabel(label)
        self.label.setStyleSheet("font-size: 12px;")
        top_row.addWidget(self.label)
        top_row.addStretch()
        self.value_label = QLabel("0%")
        self.value_label.setStyleSheet("font-size: 12px; color: #4CAF50; font-weight: bold;")
        top_row.addWidget(self.value_label)
        layout.addLayout(top_row)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(10)
        self.bar.setStyleSheet(
            "QProgressBar { border-radius: 5px; background: #e0e0e0; border: none; }"
            "QProgressBar::chunk { background: #4CAF50; border-radius: 5px; }"
        )
        layout.addWidget(self.bar)

    def set_value(self, value: int):
        self.bar.setValue(max(0, min(100, value)))
        self.value_label.setText(f"{value}%")

    def set_label(self, text: str):
        self.label.setText(text)
