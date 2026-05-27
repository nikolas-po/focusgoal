"""Окно управления привычками (ТЗ FR-003)"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QGroupBox, QScrollArea,
    QGridLayout, QMessageBox, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer
from src.config.database import SessionLocal
from src.services.habit_service import HabitService


class HabitWindow(QWidget):
    def __init__(self, user_id: int = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Привычки")
        title.setProperty("role", "pageTitle")
        layout.addWidget(title)

        self.stats_lbl = QLabel("")
        self.stats_lbl.setProperty("role", "smallText")
        layout.addWidget(self.stats_lbl)

        # Фильтры
        fg = QGroupBox("Фильтры")
        fl = QHBoxLayout(fg)
        fl.setSpacing(10)
        fl.addWidget(QLabel("Статус:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Все", "Активные", "В архиве", "Отключённые"])
        self.status_combo.setMinimumHeight(34)
        fl.addWidget(self.status_combo)
        fl.addWidget(QLabel("Тип:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Все", "Ежедневные", "Еженедельные", "Ежемесячные"])
        self.type_combo.setMinimumHeight(34)
        fl.addWidget(self.type_combo)
        ab = QPushButton("Применить")
        ab.setMinimumHeight(34)
        ab.setObjectName("primaryButton")
        ab.clicked.connect(self._load_habits)
        fl.addWidget(ab)
        rb = QPushButton("Сбросить")
        rb.setMinimumHeight(34)
        rb.setObjectName("primaryButton")
        rb.clicked.connect(self._reset_filters)
        fl.addWidget(rb)
        fl.addStretch()
        layout.addWidget(fg)

        #  Поиск по всем полям 
        search_g = QGroupBox("Поиск по всем полям")
        search_l = QHBoxLayout(search_g)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Введите текст для поиска по названию, описанию, типу, статусу…"
        )
        self.search_edit.setMinimumHeight(34)
        self.search_edit.setClearButtonEnabled(True)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._load_habits)
        self.search_edit.textChanged.connect(lambda: self._search_timer.start())
        search_l.addWidget(self.search_edit)
        clear_btn = QPushButton("✕ Очистить")
        clear_btn.setMinimumHeight(34)
        clear_btn.setFixedWidth(100)
        clear_btn.clicked.connect(lambda: self.search_edit.clear())
        search_l.addWidget(clear_btn)
        layout.addWidget(search_g)

        add_btn = QPushButton("Новая привычка")
        add_btn.setMinimumHeight(40)
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self._create_habit)
        layout.addWidget(add_btn)

        # Прокручиваемая сетка карточек
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(15)
        self.cards_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll.setWidget(self.cards_container)
        layout.addWidget(self.scroll)

        self.status_lbl = QLabel("")
        self.status_lbl.setProperty("role", "mutedSmallText")
        layout.addWidget(self.status_lbl)

    def _load_habits(self):
        # Очистить карточки
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.user_id:
            return

        si = self.status_combo.currentIndex() if hasattr(self, "status_combo") else 0
        ti = self.type_combo.currentIndex() if hasattr(self, "type_combo") else 0

        db = SessionLocal()
        try:
            svc = HabitService(db)
            habits = svc.get_habits(self.user_id)

            if si == 1: habits = [h for h in habits if h.status_id == 1]
            elif si == 2: habits = [h for h in habits if h.status_id == 2]
            elif si == 3: habits = [h for h in habits if h.status_id == 3]
            else: habits = [h for h in habits if h.status_id != 4]

            if ti > 0: habits = [h for h in habits if h.type_id == ti]

            #  Поиск по всем полям 
            search_text = self.search_edit.text().strip().lower() if hasattr(self, "search_edit") else ""
            if search_text:
                type_names = {1: "ежедневная", 2: "еженедельная", 3: "ежемесячная"}
                mode_names = {1: "бинарная", 2: "количественная"}
                status_names = {1: "активная", 2: "в архиве", 3: "отключённая", 4: "удалена"}
                def _matches(h) -> bool:
                    fields = [
                        (h.name or "").lower(),
                        (h.description or "").lower(),
                        type_names.get(h.type_id, "").lower(),
                        mode_names.get(h.mode_id, "").lower(),
                        status_names.get(h.status_id, "").lower(),
                        str(h.current_streak),
                        str(h.max_streak) if hasattr(h, "max_streak") else "",
                    ]
                    return any(search_text in f for f in fields)
                habits = [h for h in habits if _matches(h)]

            if not habits:
                from PyQt5.QtWidgets import QLabel as QL
                empty = QL("У вас пока нет привычек.\nНажмите «+ Новая привычка».")
                empty.setProperty("role", "mutedText")
                empty.setAlignment(Qt.AlignCenter)
                self.cards_layout.addWidget(empty, 0, 0, 1, 3)
                self.status_lbl.setText("Нет данных")
                return

            avg = sum(h.current_streak for h in habits) // len(habits) if habits else 0
            self.stats_lbl.setText(
                f"Привычек: {len(habits)} | Средняя серия: {avg} дн."
            )

            for i, h in enumerate(habits):
                from src.ui.widgets.habit_card import HabitCard
                progress = self._calc_progress(h)
                card = HabitCard({
                    "id": h.id, "name": h.name, "type": h.type_id,
                    "progress": progress, "streak": h.current_streak,
                    "status": h.status_id,
                })
                card.habit_completed.connect(self._on_completed)
                card.habit_edited.connect(self._on_edited)
                card.habit_deleted.connect(self._on_deleted)
                card.habit_viewed.connect(self._on_viewed)
                self.cards_layout.addWidget(card, i // 3, i % 3)

            self.status_lbl.setText(f"Найдено: {len(habits)} привычек")
        except Exception as e:
            self.status_lbl.setText(f"Ошибка: {str(e)}")
        finally:
            db.close()

    @staticmethod
    def _calc_progress(habit) -> int:
        if habit.mode_id == 1:
            return 100 if habit.current_streak > 0 else 0
        if habit.target_value and habit.target_value > 0:
            return min(100, int(habit.current_streak / habit.target_value * 100))
        return 0

    def _create_habit(self):
        from src.ui.dialogs.create_habit_dialog import CreateHabitDialog
        if CreateHabitDialog(self.user_id, self).exec_():
            self._load_habits()

    def _on_completed(self, habit_id: int):
        db = SessionLocal()
        try:
            result = HabitService(db).mark_completed(habit_id, self.user_id)
            if result:
                self._load_habits()
                QMessageBox.information(
                    self, "Отличная работа!",
                    f"Привычка выполнена!\nТекущая серия: {result.current_streak} дн."
                )
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()

    def _on_edited(self, habit_id: int):
        from src.ui.dialogs.create_habit_dialog import CreateHabitDialog
        if CreateHabitDialog(self.user_id, self, habit_id=habit_id).exec_():
            self._load_habits()

    def _on_deleted(self, habit_id: int):
        if QMessageBox.question(self, "Удалить?", "Удалить привычку?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        db = SessionLocal()
        try:
            if HabitService(db).delete_habit(habit_id, self.user_id):
                self._load_habits()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()

    def _reset_filters(self):
        self.status_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)
        if hasattr(self, "search_edit"):
            self.search_edit.clear()
        self._load_habits()

    def _on_viewed(self, habit_id: int):
        from src.ui.dialogs.habit_detail_dialog import HabitDetailDialog
        d = HabitDetailDialog(habit_id, user_id=self.user_id, parent=self)
        d.exec_()
