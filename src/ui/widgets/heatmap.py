"""Тепловая карта выполнения привычек (12 недель)"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QToolTip
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPen


class HabitHeatmap(QWidget):
    CELL_SIZE = 18
    CELL_GAP  = 3
    WEEKS     = 12
    DAYS      = 7
    MARGIN_LEFT  = 30
    MARGIN_TOP   = 30
    MARGIN_BOTTOM = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict = {}
        self._day_labels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        w = self.MARGIN_LEFT + self.WEEKS * (self.CELL_SIZE + self.CELL_GAP)
        h = (self.MARGIN_TOP + self.DAYS * (self.CELL_SIZE + self.CELL_GAP)
             + self.MARGIN_BOTTOM + 10)
        self.setMinimumSize(w, h)
        self.setMouseTracking(True)
        self._hovered = None

    def update_data(self, data: dict):
        self._data = data
        self.update()

    def _get_color(self, count: int) -> QColor:
        if count == 0:
            return QColor("#ebedf0")
        elif count == 1:
            return QColor("#9be9a8")
        elif count == 2:
            return QColor("#40c463")
        elif count <= 4:
            return QColor("#30a14e")
        else:
            return QColor("#216e39")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#555555")))

        # Дни недели (вертикально)
        for day in range(self.DAYS):
            y = (self.MARGIN_TOP + day * (self.CELL_SIZE + self.CELL_GAP)
                 + self.CELL_SIZE // 2 + 4)
            painter.drawText(0, y, self._day_labels[day])

        # Ячейки
        for week in range(self.WEEKS):
            for day in range(self.DAYS):
                count = self._data.get(f"{week}_{day}", 0)
                color = self._get_color(count)
                x = self.MARGIN_LEFT + week * (self.CELL_SIZE + self.CELL_GAP)
                y = self.MARGIN_TOP + day * (self.CELL_SIZE + self.CELL_GAP)
                rect = QRect(x, y, self.CELL_SIZE, self.CELL_SIZE)

                if self._hovered == (week, day):
                    painter.setPen(QPen(QColor("#4CAF50"), 2))
                else:
                    painter.setPen(Qt.NoPen)

                painter.setBrush(QBrush(color))
                painter.drawRoundedRect(rect, 3, 3)

        # Легенда
        legend_y = (self.MARGIN_TOP + self.DAYS * (self.CELL_SIZE + self.CELL_GAP)
                    + self.CELL_GAP + 5)
        painter.setPen(QPen(QColor("#555555")))
        painter.drawText(self.MARGIN_LEFT, legend_y + 14, "Меньше")
        x = self.MARGIN_LEFT + 60
        for count in [0, 1, 2, 3, 5]:
            painter.setBrush(QBrush(self._get_color(count)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRect(x, legend_y, 14, 14), 2, 2)
            x += 18
        painter.setPen(QPen(QColor("#555555")))
        painter.drawText(x + 2, legend_y + 14, "Больше")

    def mouseMoveEvent(self, event):
        x, y = event.x(), event.y()
        week = (x - self.MARGIN_LEFT) // (self.CELL_SIZE + self.CELL_GAP)
        day  = (y - self.MARGIN_TOP)  // (self.CELL_SIZE + self.CELL_GAP)
        if 0 <= week < self.WEEKS and 0 <= day < self.DAYS:
            self._hovered = (week, day)
            count = self._data.get(f"{week}_{day}", 0)
            QToolTip.showText(event.globalPos(),
                              f"Неделя {week+1}, {self._day_labels[day]}: {count} выполн.")
        else:
            self._hovered = None
        self.update()

    def leaveEvent(self, event):
        self._hovered = None
        self.update()
