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
        self.label.setProperty("role", "smallText")
        top_row.addWidget(self.label)
        top_row.addStretch()
        self.value_label = QLabel("0%")
        self.value_label.setProperty("role", "accentBoldText")
        top_row.addWidget(self.value_label)
        layout.addLayout(top_row)

        self.bar = QProgressBar()
        self.bar.setObjectName("smallProgressBar")
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(10)
        layout.addWidget(self.bar)

    def set_value(self, value: int):
        self.bar.setValue(max(0, min(100, value)))
        self.value_label.setText(f"{value}%")

    def set_label(self, text: str):
        self.label.setText(text)
