"""Управление чёрным списком приложений (ТЗ FR-009)"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
    QGroupBox, QMessageBox, QHeaderView, QFormLayout, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from src.config.database import SessionLocal
from src.repositories.blocked_app_repository import BlockedAppRepository
from src.utils.process_monitor import ProcessMonitor


class BlacklistWindow(QWidget):
    def __init__(self, user_id: int = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.monitor = ProcessMonitor()
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Чёрный список приложений")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel(
            "Приложения из этого списка блокируются во время фокус-сессии.\n"
            "Уровень «Полная блокировка» требует прав администратора."
        )
        desc.setStyleSheet("font-size: 12px; color: palette(mid);")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # ── Форма добавления ────────────────────────────────────────────────
        add_g = QGroupBox("Добавить приложение")
        fl = QFormLayout(add_g)
        fl.setSpacing(10)
        fl.setLabelAlignment(Qt.AlignRight)

        self.app_name_input = QLineEdit()
        self.app_name_input.setPlaceholderText("Название (например: Chrome)")
        self.app_name_input.setMinimumHeight(36)
        fl.addRow("Название:", self.app_name_input)

        self.process_input = QLineEdit()
        self.process_input.setPlaceholderText("Имя процесса (например: chrome)")
        self.process_input.setMinimumHeight(36)
        fl.addRow("Процесс:", self.process_input)

        self.level_combo = QComboBox()
        self.level_combo.addItems([
            "Полная блокировка (требует sudo)",
            "Уведомление при открытии",
            "Ограничение времени",
        ])
        self.level_combo.setMinimumHeight(36)
        fl.addRow("Уровень:", self.level_combo)

        add_btn = QPushButton("➕ Добавить в список")
        add_btn.setMinimumHeight(38)
        add_btn.clicked.connect(self._add_app)
        fl.addRow(add_btn)
        layout.addWidget(add_g)

        # ── Быстрый выбор ───────────────────────────────────────────────────
        quick_g = QGroupBox("Быстрый выбор из запущенных процессов")
        ql = QHBoxLayout(quick_g)
        self.proc_combo = QComboBox()
        self.proc_combo.setMinimumHeight(36)
        self.proc_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        ql.addWidget(self.proc_combo)

        for text, slot in [("🔄", self._refresh_processes), ("Добавить", self._quick_add)]:
            b = QPushButton(text)
            b.setMinimumHeight(36)
            b.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            b.clicked.connect(slot)
            ql.addWidget(b)
        layout.addWidget(quick_g)

        # ── Таблица ─────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID","Приложение","Процесс","Уровень",""])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 90)          # фиксированная ширина для кнопки
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(220)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.table, stretch=1)

        scroll.setWidget(container)
        outer.addWidget(scroll)
        self._refresh_processes()

    def _refresh_processes(self):
        self.proc_combo.clear()
        seen = set()
        for p in sorted(self.monitor.get_running_processes(), key=lambda x: x["name"].lower()):
            name = p["name"]
            if name and name.lower() not in seen and not name.startswith("["):
                seen.add(name.lower())
                self.proc_combo.addItem(name, name)

    def _quick_add(self):
        name = self.proc_combo.currentData()
        if name:
            self.app_name_input.setText(name)
            self.process_input.setText(name)

    def _add_app(self):
        app_name  = self.app_name_input.text().strip()
        proc_name = self.process_input.text().strip()
        level_id  = self.level_combo.currentIndex() + 1
        if not app_name or not proc_name:
            QMessageBox.warning(self, "Ошибка", "Заполните название и имя процесса"); return
        db = SessionLocal()
        try:
            repo = BlockedAppRepository(db)
            if any(a.process_name.lower() == proc_name.lower() for a in repo.get_by_user(self.user_id)):
                QMessageBox.warning(self, "Уже есть", f"Процесс «{proc_name}» уже в списке"); return
            repo.create(user_id=self.user_id, app_name=app_name,
                        process_name=proc_name, block_level_id=level_id, is_active=True)
            self.app_name_input.clear(); self.process_input.clear()
            self._load()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally: db.close()

    def _load(self):
        self.table.setRowCount(0)
        db = SessionLocal()
        try:
            level_names = {1: "Полная", 2: "Уведомление", 3: "Лимит"}
            for i, app in enumerate(BlockedAppRepository(db).get_by_user(self.user_id)):
                self.table.insertRow(i)
                for col, val in enumerate([str(app.id), app.app_name, app.process_name,
                                           level_names.get(app.block_level_id,"?")]):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                    self.table.setItem(i, col, item)

                # Кнопка удаления — фиксированный размер, вписывается в ячейку
                del_btn = QPushButton("🗑 Удалить")
                del_btn.setFixedHeight(28)
                del_btn.setStyleSheet(
                    "QPushButton{background:#FF5252;color:white;border:none;"
                    "border-radius:4px;padding:0 6px;font-size:11px;}"
                    "QPushButton:hover{background:#E53935;}"
                )
                del_btn.clicked.connect(lambda _, aid=app.id: self._delete_app(aid))
                # Центрировать кнопку в ячейке
                cell_w = QWidget()
                cell_l = QHBoxLayout(cell_w)
                cell_l.setContentsMargins(4, 2, 4, 2)
                cell_l.addWidget(del_btn)
                self.table.setCellWidget(i, 4, cell_w)
                self.table.setRowHeight(i, 36)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally: db.close()

    def _delete_app(self, app_id: int):
        if QMessageBox.question(self,"Удалить?","Убрать из чёрного списка?",
                                QMessageBox.Yes|QMessageBox.No) != QMessageBox.Yes: return
        db = SessionLocal()
        try:
            BlockedAppRepository(db).delete(app_id); self._load()
        except Exception as e:
            QMessageBox.warning(self,"Ошибка",str(e))
        finally: db.close()
