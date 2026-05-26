from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from src.config.database import SessionLocal
from src.repositories.habit_repository import HabitRepository
from src.repositories.notification_repository import NotificationRepository


class HabitDetailDialog(QDialog):
    def __init__(self, habit_id: int, user_id: int = None, parent=None):
        super().__init__(parent)
        self.habit_id = habit_id
        self.user_id = user_id
        self.setWindowTitle("Детали привычки")
        self.setMinimumWidth(420)
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.name_lbl = QLabel("")
        self.name_lbl.setProperty("role", "boldText")
        self.layout.addWidget(self.name_lbl)

        self.type_lbl = QLabel("")
        self.layout.addWidget(self.type_lbl)

        self.status_lbl = QLabel("")
        self.layout.addWidget(self.status_lbl)

        self.streak_lbl = QLabel("")
        self.layout.addWidget(self.streak_lbl)

        self.desc_lbl = QLabel("")
        self.desc_lbl.setWordWrap(True)
        self.layout.addWidget(self.desc_lbl)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        self.layout.addWidget(close_btn)

    def _load(self):
        db = SessionLocal()
        try:
            repo = HabitRepository(db)
            habit = repo.get_by_id(self.habit_id)
            if not habit:
                self.name_lbl.setText("Привычка не найдена")
                return
            type_map = {1: "Ежедневная", 2: "Еженедельная", 3: "Ежемесячная"}
            status_map = {1: "Активна", 2: "В архиве", 3: "Отключена", 4: "Удалена"}
            self.name_lbl.setText(habit.name)
            self.type_lbl.setText(f"Тип: {type_map.get(habit.type_id, habit.type_id)}")
            self.status_lbl.setText(f"Статус: {status_map.get(habit.status_id, habit.status_id)}")
            self.streak_lbl.setText(f"Серия: {habit.current_streak} | Макс: {habit.max_streak}")
            self.desc_lbl.setText(habit.description or "(Описание отсутствует)")
            # Показать напоминания, связанные с привычкой (по вхождению названия)
            try:
                notif_repo = NotificationRepository(db)
                notifs_all = notif_repo.get_by_user(self.user_id) if self.user_id else notif_repo.get_by_user(habit.user_id)
                notifs = [n for n in notifs_all if habit.name and habit.name in (n.content or "")]
            except Exception:
                notifs = []
            if notifs:
                nl = "\n".join([f"{n.send_at}: {n.content} ({'Отправлено' if n.delivery_status_id==3 else 'Ожидает'})" for n in notifs])
                self.layout.addWidget(QLabel("Напоминания:"))
                lbl = QLabel(nl)
                lbl.setWordWrap(True)
                self.layout.addWidget(lbl)
        finally:
            db.close()
