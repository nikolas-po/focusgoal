"""Управление целями (ТЗ FR-003)"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox,
    QMessageBox, QHeaderView, QGroupBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from src.config.database import SessionLocal
from src.repositories.goal_repository import GoalRepository
from src.ui.dialogs.create_goal_dialog import CreateGoalDialog


class GoalWindow(QWidget):
    def __init__(self, user_id: int = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self._setup_ui()
        self.load_goals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("Управление целями")
        title_font = QFont("Arial", 18, QFont.Bold)
        title.setFont(title_font)
        layout.addWidget(title)

        # Фильтры
        filter_g = QGroupBox("Фильтры")
        filter_l = QHBoxLayout(filter_g)
        
        filter_l.addWidget(QLabel("Статус:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Все", "Активные", "Выполненные", "Просроченные"])
        self.status_combo.currentIndexChanged.connect(self.load_goals)
        filter_l.addWidget(self.status_combo)
        
        filter_l.addWidget(QLabel("Приоритет:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Любой", "Высокий", "Средний", "Низкий"])
        self.priority_combo.currentIndexChanged.connect(self.load_goals)
        filter_l.addWidget(self.priority_combo)
        
        filter_l.addStretch()
        layout.addWidget(filter_g)

        # Кнопки действий - горизонтально в одну строку
        actions_l = QHBoxLayout()
        actions_l.setSpacing(10)
        actions_l.setContentsMargins(0, 0, 0, 0)

        self.add_btn = QPushButton("Новая цель")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setMinimumWidth(140)
        self.add_btn.clicked.connect(self._create)
        actions_l.addWidget(self.add_btn)

        self.edit_btn = QPushButton("Редактировать")
        self.edit_btn.setMinimumHeight(40)
        self.edit_btn.setMinimumWidth(140)
        self.edit_btn.clicked.connect(self._edit)
        actions_l.addWidget(self.edit_btn)

        self.mark_btn = QPushButton("Выполнено")
        self.mark_btn.setMinimumHeight(40)
        self.mark_btn.setMinimumWidth(140)
        self.mark_btn.clicked.connect(self._mark_done)
        actions_l.addWidget(self.mark_btn)

        self.view_btn = QPushButton("Просмотр")
        self.view_btn.setMinimumHeight(40)
        self.view_btn.setMinimumWidth(140)
        self.view_btn.clicked.connect(self._view)
        actions_l.addWidget(self.view_btn)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.setMinimumHeight(40)
        self.delete_btn.setMinimumWidth(140)
        self.delete_btn.setObjectName("dangerButton")
        self.delete_btn.clicked.connect(self._delete)
        actions_l.addWidget(self.delete_btn)

        actions_l.addStretch()
        layout.addLayout(actions_l)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["№", "Название", "Дедлайн", "Приоритет", "Статус", "Описание"])
        
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.Stretch)
        
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setMinimumHeight(300)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(True)
        layout.addWidget(self.table, stretch=1)

    def load_goals(self):
        """Загрузить цели из БД (вызывается из main_window)"""
        self.table.setRowCount(0)
        db = SessionLocal()
        try:
            repo = GoalRepository(db)
            goals = repo.get_by_user(self.user_id)
            
            if not goals:
                return
            
            status_filter = self.status_combo.currentText()
            priority_filter = self.priority_combo.currentText()
            
            row = 0
            for goal in goals:
                # Применить фильтры
                if status_filter != "Все":
                    status_map = {"Активные": 1, "Выполненные": 2, "Просроченные": 3}
                    if goal.status_id != status_map.get(status_filter):
                        continue
                
                if priority_filter != "Любой":
                    priority_map = {"Высокий": 1, "Средний": 2, "Низкий": 3}
                    if goal.priority_id != priority_map.get(priority_filter):
                        continue
                
                self.table.insertRow(row)
                
                # Порядковый номер (не редактируемый), реальный id хранится в UserRole
                id_item = QTableWidgetItem(str(row + 1))
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                id_item.setData(Qt.UserRole, goal.id)
                self.table.setItem(row, 0, id_item)
                
                # Название
                self.table.setItem(row, 1, QTableWidgetItem(goal.name or ""))
                
                # Дедлайн
                deadline_str = goal.deadline.date().strftime("%d.%m.%Y") if goal.deadline else ""
                self.table.setItem(row, 2, QTableWidgetItem(deadline_str))
                
                # Приоритет
                priority_names = {1: "Высокий", 2: "Средний", 3: "Низкий"}
                self.table.setItem(row, 3, QTableWidgetItem(priority_names.get(goal.priority_id, "?")))
                
                # Статус
                status_names = {
                    1: "Активная",
                    2: "Выполнена",
                    3: "Просрочена",
                    4: "Отменена"
                }
                self.table.setItem(row, 4, QTableWidgetItem(status_names.get(goal.status_id, "?")))
                
                # Описание
                self.table.setItem(row, 5, QTableWidgetItem(goal.description or ""))
                
                row += 1
                # Подогнать высоту строк под содержимое (перенос строк включён)
                try:
                    self.table.resizeRowsToContents()
                except Exception:
                    pass
        except Exception as e:
            QMessageBox.warning(self, "Ошибка загрузки", f"Не удалось загрузить цели:\n{e}")
        finally:
            db.close()

    def _get_selected_id(self) -> int:
        """Получить ID выбранной цели"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите цель из таблицы")
            return None
        try:
            item = self.table.item(row, 0)
            if item:
                goal_id = item.data(Qt.UserRole)
                return int(goal_id)
        except (ValueError, AttributeError):
            pass
        return None

    def _view(self):
        """Показать детали выбранной цели"""
        goal_id = self._get_selected_id()
        if not goal_id:
            return
        try:
            from src.ui.dialogs.goal_detail_dialog import GoalDetailDialog
            db = SessionLocal()
            try:
                repo = GoalRepository(db)
                goal = repo.get_by_id(goal_id)
                if not goal:
                    QMessageBox.warning(self, "Ошибка", "Цель не найдена")
                    return
                goal_data = {
                    "id": goal.id,
                    "name": goal.name,
                    "description": goal.description,
                    "deadline": goal.deadline,
                    "priority_id": goal.priority_id,
                    "status_id": goal.status_id,
                    "repeat_type_id": getattr(goal, 'repeat_type_id', None),
                    "fail_behavior_id": getattr(goal, 'fail_behavior_id', None),
                    "created_at": getattr(goal, 'created_at', None),
                }
            finally:
                db.close()

            dlg = GoalDetailDialog(goal_data, user_id=self.user_id, parent=self)
            if dlg.exec_():
                self.load_goals()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть просмотр цели:\n{e}")

    def _create(self):
        """Создать новую цель"""
        dlg = CreateGoalDialog(self.user_id, self)
        if dlg.exec_():
            self.load_goals()

    def _edit(self):
        """Редактировать выбранную цель"""
        goal_id = self._get_selected_id()
        if not goal_id:
            return
        dlg = CreateGoalDialog(self.user_id, self, goal_id=goal_id)
        if dlg.exec_():
            self.load_goals()

    def _mark_done(self):
        """Отметить цель выполненной"""
        goal_id = self._get_selected_id()
        if not goal_id:
            return
        db = SessionLocal()
        try:
            repo = GoalRepository(db)
            goal = repo.get_by_id(goal_id)
            if goal:
                goal.status_id = 2  # выполнена
                db.commit()
                QMessageBox.information(self, "Успех", f"Цель '{goal.name}' отмечена выполненной")
                self.load_goals()
            else:
                QMessageBox.warning(self, "Ошибка", "Цель не найдена")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при отметке цели:\n{e}")
            db.rollback()
        finally:
            db.close()

    def _delete(self):
        """Удалить цель"""
        goal_id = self._get_selected_id()
        if not goal_id:
            return
        
        # Получить название цели для подтверждения
        row = self.table.currentRow()
        goal_name = self.table.item(row, 1).text() if row >= 0 else "эту цель"
        
        reply = QMessageBox.question(
            self,
            "Удалить цель?",
            f"Вы уверены что хотите удалить цель '{goal_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        
        db = SessionLocal()
        try:
            GoalRepository(db).delete(goal_id)
            QMessageBox.information(self, "Успех", f"Цель '{goal_name}' удалена")
            self.load_goals()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при удалении цели:\n{e}")
            db.rollback()
        finally:
            db.close()