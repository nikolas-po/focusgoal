"""Диалог импорта данных (ТЗ FR-011)"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QComboBox, QCheckBox,
    QFileDialog, QMessageBox, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt
from src.config.database import SessionLocal
from src.services.import_service import ImportService


class ImportDialog(QDialog):
    def __init__(self, user_id: int = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.file_path = ""
        self.setWindowTitle("Импорт данных")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setMinimumHeight(520)
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(14)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("Импорт данных")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        warn = QLabel(
            "Перед импортом рекомендуется создать резервную копию. "
            "При конфликтах данные обрабатываются согласно выбранному режиму."
        )
        warn.setStyleSheet("color: #FF5252; font-size: 12px; font-weight: bold;")
        warn.setWordWrap(True)
        layout.addWidget(warn)

        # Файл
        file_g = QGroupBox("Файл для импорта")
        fl = QVBoxLayout(file_g)
        sel_btn = QPushButton("Выбрать файл")
        sel_btn.setMinimumHeight(42)
        sel_btn.clicked.connect(self._select_file)
        fl.addWidget(sel_btn)
        self.file_label = QLabel("Файл не выбран")
        self.file_label.setStyleSheet("color: #888; font-style: italic; font-size: 12px;")
        self.file_label.setWordWrap(True)
        fl.addWidget(self.file_label)
        layout.addWidget(file_g)

        # Режим
        mode_g = QGroupBox("Режим при дубликатах")
        ml = QVBoxLayout(mode_g)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Добавить новые записи (пропустить существующие)",
            "Заменить существующие записи",
            "Пропустить все дубликаты",
        ])
        self.mode_combo.setMinimumHeight(40)
        ml.addWidget(self.mode_combo)
        layout.addWidget(mode_g)

        # Безопасность
        sec_g = QGroupBox("Безопасность")
        sl = QVBoxLayout(sec_g)
        self.backup_check = QCheckBox("Создать резервную копию перед импортом (рекомендуется)")
        self.backup_check.setChecked(True)
        sl.addWidget(self.backup_check)
        layout.addWidget(sec_g)

        layout.addStretch()

        btn_row = QHBoxLayout()
        import_btn = QPushButton("Импортировать")
        import_btn.setMinimumHeight(48)
        import_btn.clicked.connect(self._import)
        btn_row.addWidget(import_btn)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumHeight(48)
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        container.setLayout(layout)
        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.addWidget(scroll)

        self.setStyleSheet("""
            QDialog { background: palette(window); }
            QGroupBox { font-weight: bold; border: 1px solid palette(mid);
                        border-radius: 8px; margin-top: 8px; padding-top: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            QPushButton { background: #2196F3; color: white; border: none;
                          border-radius: 4px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background: #1976D2; }
            QPushButton#cancelButton { background: #9E9E9E; }
        """)

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать файл",
            "",
            "JSON/CSV Files (*.json *.csv);;All Files (*)"
        )
        if path:
            self.file_path = path
            self.file_label.setText(path)
            self.file_label.setStyleSheet("color: #4CAF50; font-size: 12px;")

    def _import(self):
        if not self.file_path:
            QMessageBox.warning(self, "Ошибка", "Выберите файл для импорта")
            return
        mode_map = {0: "add", 1: "replace", 2: "skip"}
        mode = mode_map.get(self.mode_combo.currentIndex(), "add")
        db = SessionLocal()
        try:
            svc = ImportService(db, self.user_id)
            if self.file_path.lower().endswith(".csv"):
                result = svc.import_from_csv(self.file_path)
            else:
                result = svc.import_from_json(self.file_path, mode=mode)
            msg = (
                f"Импорт завершён!\n\n"
                f"Целей импортировано: {result['imported_goals']}\n"
                f"Привычек импортировано: {result['imported_habits']}\n"
                f"Пропущено: {result.get('skipped', 0)}\n"
                f"Заменено: {result.get('replaced', 0)}"
            )
            errs = result.get("errors", [])
            if errs:
                msg += f"\n\nОшибок: {len(errs)}\n" + "\n".join(errs[:3])
                if len(errs) > 3:
                    msg += f"\n...и ещё {len(errs)-3}"
            QMessageBox.information(self, "Результат", msg)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка импорта", str(e))
        finally:
            db.close()
