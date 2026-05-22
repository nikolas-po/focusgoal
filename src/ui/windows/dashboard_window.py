"""Главная панель / дашборд (ТЗ FR-005)"""
from datetime import datetime, timezone
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from src.config.database import SessionLocal
from src.services.statistics_service import StatisticsService


class DashboardWindow(QWidget):
    def __init__(self, user_id: int = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self._setup_ui()
        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self.load_statistics)
        self._auto_timer.start(60_000)

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent;")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Заголовок
        header = QHBoxLayout()
        title = QLabel("Главная панель")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        refresh_btn = QPushButton("Обновить")
        refresh_btn.setMaximumWidth(120)
        refresh_btn.clicked.connect(self.load_statistics)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        date_lbl = QLabel(f"Сегодня: {datetime.now().strftime('%d.%m.%Y')}")
        date_lbl.setStyleSheet("font-size: 12px; color: palette(mid);")
        layout.addWidget(date_lbl)

        # Карточки статистики
        grid = QGridLayout()
        grid.setSpacing(15)
        self.goals_card       = self._make_card("🎯 Цели",       "0", "всего")
        self.habits_card      = self._make_card("✅ Привычки",    "0", "активных")
        self.focus_card       = self._make_card("🔒 Фокус",      "0ч 0м", "суммарно")
        self.productivity_card = self._make_card("📊 Прогресс",  "0%", "выполнения")
        grid.addWidget(self.goals_card,        0, 0)
        grid.addWidget(self.habits_card,       0, 1)
        grid.addWidget(self.focus_card,        1, 0)
        grid.addWidget(self.productivity_card, 1, 1)
        layout.addLayout(grid)

        # Быстрые действия
        qa_label = QLabel("Быстрые действия")
        qa_label.setStyleSheet("font-size: 16px; font-weight: bold; color: palette(text);")
        layout.addWidget(qa_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        for text, color, handler in [
            ("+ Новая цель",   "#4CAF50", self._quick_goal),
            ("+ Привычка",     "#2196F3", self._quick_habit),
            ("Фокус",       "#FF9800", self._quick_focus),
            ("Статистика",  "#9C27B0", self._quick_stats),
        ]:
            btn = QPushButton(text)
            btn.setMinimumHeight(44)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet(
                f"QPushButton {{ background: {color}; color: white; border: none; "
                f"border-radius: 6px; font-weight: bold; padding: 10px; }}"
                f"QPushButton:hover {{ opacity: 0.85; }}"
            )
            btn.clicked.connect(handler)
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

        # Последние события
        ev_title = QLabel("Последние события")
        ev_title.setStyleSheet("font-size: 16px; font-weight: bold; color: palette(text);")
        layout.addWidget(ev_title)

        self.events_label = QLabel("Нет данных")
        self.events_label.setStyleSheet(
            "font-size: 12px; padding: 10px; border-radius: 6px; color: palette(mid);"
        )
        self.events_label.setWordWrap(True)
        self.events_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(self.events_label)
        layout.addStretch()

        container.setLayout(layout)
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def _make_card(self, title: str, value: str, subtitle: str) -> QFrame:
        card = QFrame()
        card.setObjectName("statCard")
        card.setMinimumHeight(110)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(15, 12, 15, 12)
        cl.setSpacing(4)

        tl = QLabel(title)
        tl.setStyleSheet("font-size: 13px; color: palette(mid);")
        cl.addWidget(tl)

        vl = QLabel(value)
        vl.setObjectName("valueLabel")
        vl.setStyleSheet("font-size: 26px; font-weight: bold;")
        cl.addWidget(vl)

        sl = QLabel(subtitle)
        sl.setObjectName("subtitleLabel")
        sl.setStyleSheet("font-size: 11px; color: palette(mid);")
        cl.addWidget(sl)
        return card

    def load_statistics(self):
        if not self.user_id:
            return
        db = SessionLocal()
        try:
            svc = StatisticsService(db)
            st = svc.get_dashboard_statistics(self.user_id)
            self._set_card(self.goals_card,
                           str(st["goals"]["total"]),
                           f"выполнено: {st['goals']['completed']}")
            self._set_card(self.habits_card,
                           str(st["habits"]["active"]),
                           f"всего: {st['habits']['total']}")
            h = st["focus"]["total_minutes"] // 60
            m = st["focus"]["total_minutes"] % 60
            self._set_card(self.focus_card, f"{h}ч {m}м",
                           f"сессий: {st['focus']['sessions_total']}")
            self._set_card(self.productivity_card,
                           f"{st['goals']['rate']:.0f}%", "успешных целей")
            events = self._get_events(db)
            self.events_label.setText(events)
        except Exception:
            pass
        finally:
            db.close()

    def _set_card(self, card: QFrame, value: str, subtitle: str = ""):
        for lbl in card.findChildren(QLabel):
            if lbl.objectName() == "valueLabel":
                lbl.setText(value)
            elif lbl.objectName() == "subtitleLabel" and subtitle:
                lbl.setText(subtitle)

    def _get_events(self, db) -> str:
        try:
            from src.models.completion_log import CompletionLog
            logs = (db.query(CompletionLog)
                    .filter(CompletionLog.user_id == self.user_id)
                    .order_by(CompletionLog.completed_at.desc())
                    .limit(5).all())
            if not logs:
                return "• Нет недавних событий"
            lines = []
            for log in logs:
                dt = log.completed_at.strftime("%d.%m %H:%M")
                obj = "Цель" if log.object_type_id == 1 else "Привычка"
                lines.append(f"• {dt} — {obj} выполнена")
            return "\n".join(lines)
        except Exception:
            return "• Нет данных"

    def _quick_goal(self):
        from src.ui.dialogs.create_goal_dialog import CreateGoalDialog
        CreateGoalDialog(self.user_id, self).exec_()
        self.load_statistics()

    def _quick_habit(self):
        from src.ui.dialogs.create_habit_dialog import CreateHabitDialog
        CreateHabitDialog(self.user_id, self).exec_()
        self.load_statistics()

    def _quick_focus(self):
        tabs = self._find_tab_widget()
        if tabs:
            tabs.setCurrentIndex(3)

    def _quick_stats(self):
        tabs = self._find_tab_widget()
        if tabs:
            tabs.setCurrentIndex(4)

    def _find_tab_widget(self):
        from PyQt5.QtWidgets import QTabWidget
        parent = self.parentWidget()
        while parent:
            if isinstance(parent, QTabWidget):
                return parent
            parent = parent.parentWidget()
        if self.window():
            return self.window().findChild(QTabWidget)
        return None


    def _start_focus(self):
        """Запустить фокус с главной"""
        try:
            main = self.parentWidget()
            while main and not hasattr(main, "focus_tab"): main = main.parentWidget()
            if main: main.tabs.setCurrentWidget(main.focus_tab)
        except: pass
    
    def _show_stats(self):
        """Показать статистику"""
        try:
            main = self.parentWidget()
            while main and not hasattr(main, "stats_tab"): main = main.parentWidget()
            if main: main.tabs.setCurrentWidget(main.stats_tab)
        except: pass