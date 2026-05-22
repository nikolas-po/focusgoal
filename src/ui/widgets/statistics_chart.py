"""Виджет графиков статистики (matplotlib + PyQt5)"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QLabel
from PyQt5.QtCore import Qt
from typing import List

try:
    import matplotlib
    matplotlib.use("Qt5Agg")
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    matplotlib.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Liberation Sans"],
        "font.size": 10,
        "axes.unicode_minus": False,
    })
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    FigureCanvas = QWidget


def _theme_colors() -> dict:
    """Цвета в зависимости от текущей темы (через theme_state)."""
    try:
        from src.config import theme_state
        dark = theme_state.current_theme == "Тёмная"
    except Exception:
        dark = False
    if dark:
        return {"bg": "#2b2b2b", "axes_bg": "#363636", "text": "#e0e0e0",
                "grid": "#444444", "spine": "#555555"}
    return {"bg": "#ffffff", "axes_bg": "#ffffff", "text": "#212121",
            "grid": "#e0e0e0", "spine": "#cccccc"}


class StatisticsChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._canvas = None
        self._fig = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        if HAS_MPL:
            c = _theme_colors()
            self._fig = Figure(figsize=(6, 3), tight_layout=True, facecolor=c["bg"])
            self._canvas = FigureCanvas(self._fig)
            self._canvas.setStyleSheet("background: transparent;")
            self._layout.addWidget(self._canvas)
        else:
            lbl = QLabel("matplotlib не установлен")
            lbl.setAlignment(Qt.AlignCenter)
            self._layout.addWidget(lbl)

    def _clear(self):
        if self._fig:
            self._fig.clear()

    def _apply_theme(self, ax):
        c = _theme_colors()
        self._fig.patch.set_facecolor(c["bg"])
        ax.set_facecolor(c["axes_bg"])
        ax.title.set_color(c["text"])
        ax.xaxis.label.set_color(c["text"])
        ax.yaxis.label.set_color(c["text"])
        ax.tick_params(colors=c["text"], which="both")
        for spine in ax.spines.values():
            spine.set_color(c["spine"])
        ax.grid(True, color=c["grid"], alpha=0.4, linewidth=0.5)

    def plot_bar_chart(self, labels: List[str], values: List[int], title: str = ""):
        if not HAS_MPL: return
        self._clear()
        ax = self._fig.add_subplot(111)
        self._apply_theme(ax)
        if labels and values:
            short = [l[-5:] if len(l) > 7 else l for l in labels]
            bars = ax.bar(short, values, color="#4CAF50", alpha=0.85, zorder=3)
            ax.bar_label(bars, padding=2, color=_theme_colors()["text"], fontsize=8)
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                    transform=ax.transAxes, fontsize=12,
                    color=_theme_colors()["text"], alpha=0.5)
        ax.set_title(title, fontsize=11, color=_theme_colors()["text"])
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        self._canvas.draw()

    def plot_line_chart(self, labels: List[str], values: List[int], title: str = ""):
        if not HAS_MPL: return
        self._clear()
        ax = self._fig.add_subplot(111)
        self._apply_theme(ax)
        if labels and values:
            short = [l[-5:] if len(l) > 7 else l for l in labels]
            ax.plot(short, values, color="#2196F3", linewidth=2,
                    marker="o", markersize=5, zorder=3)
            ax.fill_between(range(len(values)), values, alpha=0.12, color="#2196F3")
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                    transform=ax.transAxes, fontsize=12,
                    color=_theme_colors()["text"], alpha=0.5)
        ax.set_title(title, fontsize=11, color=_theme_colors()["text"])
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        self._canvas.draw()

    def plot_pie_chart(self, labels: List[str], values: List[int], title: str = ""):
        if not HAS_MPL: return
        self._clear()
        ax = self._fig.add_subplot(111)
        self._apply_theme(ax)
        c = _theme_colors()
        safe_labels = [_strip_emoji(l) for l in labels]
        total = sum(values)
        if total > 0:
            colors = ["#4CAF50", "#FF5252", "#FF9800", "#2196F3", "#9C27B0"]
            wedge = {"edgecolor": c["bg"], "linewidth": 2}
            ax.pie(values, labels=safe_labels, autopct="%1.0f%%",
                   colors=colors[:len(values)], wedgeprops=wedge, startangle=90,
                   textprops={"color": c["text"], "fontsize": 9},
                   pctdistance=0.75, labeldistance=1.05)
            ax.axis("equal")
        else:
            ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                    transform=ax.transAxes, fontsize=12, color=c["text"], alpha=0.5)
        ax.set_title(title, fontsize=11, color=c["text"])
        self._canvas.draw()

    def refresh_theme(self):
        """Перерисовать текущий график с новыми цветами темы."""
        if self._fig and self._canvas:
            c = _theme_colors()
            self._fig.patch.set_facecolor(c["bg"])
            for ax in self._fig.get_axes():
                self._apply_theme(ax)
            self._canvas.draw()


def _strip_emoji(s: str) -> str:
    replacements = {
        "✅": "Выполнено", "⏹": "Прервано", "❗": "Внешне",
        "🔒": "Фокус", "🚀": "Запуск", "⚠️": "Внимание",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s
