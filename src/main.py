"""Точка входа GUI FocusGoal (временная заглушка)"""
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

def main():
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("FocusGoal")
    layout = QVBoxLayout()
    label = QLabel("FocusGoal - интерфейс в разработке\n\nБаза данных инициализирована.\nГрафический интерфейс появится после добавления окон.")
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    window.setLayout(layout)
    window.resize(500, 300)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()