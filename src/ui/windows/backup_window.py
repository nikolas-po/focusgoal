"""Окно управления резервными копиями (ТЗ FR-010)"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QListWidget, QListWidgetItem,
    QProgressBar, QScrollArea, QFormLayout, QTimeEdit,
    QSpinBox, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt, QTime
from pathlib import Path
from datetime import datetime
from src.config.database import SessionLocal
from src.services.backup_service import BackupService


class BackupWindow(QWidget):
    def __init__(self, user_id: int = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self._selected_path = None
        self._setup_ui()
        self._load_backups()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(18)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("Резервные копии")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel(
            "Регулярно создавайте резервные копии для защиты данных. "
            "Хранятся последние 7 копий по умолчанию."
        )
        desc.setStyleSheet("font-size: 12px; color: #666;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Список бэкапов
        list_g = QGroupBox("Доступные резервные копии")
        list_l = QVBoxLayout(list_g)

        self.backup_list = QListWidget()
        self.backup_list.setMinimumHeight(180)
        self.backup_list.itemClicked.connect(self._on_selected)
        list_l.addWidget(self.backup_list)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.restore_btn = QPushButton("Восстановить")
        self.restore_btn.setMinimumHeight(40)
        self.restore_btn.setEnabled(False)
        self.restore_btn.clicked.connect(self._restore)
        btn_row.addWidget(self.restore_btn)

        self.del_btn = QPushButton("Удалить")
        self.del_btn.setMinimumHeight(40)
        self.del_btn.setEnabled(False)
        self.del_btn.setObjectName("dangerButton")
        self.del_btn.clicked.connect(self._delete_backup)
        btn_row.addWidget(self.del_btn)

        refresh_btn = QPushButton("Обновить список")
        refresh_btn.setMinimumHeight(40)
        refresh_btn.clicked.connect(self._load_backups)
        btn_row.addWidget(refresh_btn)
        list_l.addLayout(btn_row)
        layout.addWidget(list_g)

        # Информация о выбранной копии
        self.info_g = QGroupBox("Информация о копии")
        info_l = QVBoxLayout(self.info_g)
        self.info_label = QLabel("Выберите копию из списка")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("font-size: 12px; color: #666;")
        info_l.addWidget(self.info_label)
        layout.addWidget(self.info_g)

        # Прогресс
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(18)
        layout.addWidget(self.progress_bar)

        self.progress_lbl = QLabel("")
        self.progress_lbl.setVisible(False)
        layout.addWidget(self.progress_lbl)

        # Автоматическое резервное копирование
        auto_g = QGroupBox("Автоматическое резервное копирование")
        auto_l = QFormLayout(auto_g)

        self.auto_check = QCheckBox("Создавать резервную копию ежедневно")
        self.auto_check.setChecked(True)
        auto_l.addRow(self.auto_check)

        self.auto_time = QTimeEdit()
        self.auto_time.setTime(QTime(2, 0))
        self.auto_time.setMinimumHeight(38)
        auto_l.addRow("Время создания:", self.auto_time)

        self.keep_count = QSpinBox()
        self.keep_count.setRange(1, 30)
        self.keep_count.setValue(7)
        self.keep_count.setMinimumHeight(38)
        auto_l.addRow("Хранить копий (макс):", self.keep_count)
        layout.addWidget(auto_g)

        layout.addStretch()

        # Кнопка создания
        create_btn = QPushButton("Создать резервную копию сейчас")
        create_btn.setMinimumHeight(54)
        create_btn.setStyleSheet(
            "QPushButton { font-size: 16px; font-weight: bold; "
            "background: #4CAF50; color: white; border: none; border-radius: 8px; }"
            "QPushButton:hover { background: #45a049; }"
        )
        create_btn.clicked.connect(self._create_now)
        layout.addWidget(create_btn)

        container.setLayout(layout)
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def _load_backups(self):
        self.backup_list.clear()
        self._selected_path = None
        self.restore_btn.setEnabled(False)
        self.del_btn.setEnabled(False)

        db = SessionLocal()
        try:
            svc = BackupService(db)
            backups = svc.list_backups()
            if not backups:
                item = QListWidgetItem("Резервных копий нет")
                item.setFlags(Qt.NoItemFlags)
                self.backup_list.addItem(item)
                return
            for b in backups:
                item = QListWidgetItem(
                    f"{b['date']}  —  {b['size_mb']} MB  —  {b['name']}"
                )
                item.setData(Qt.UserRole, b["path"])
                self.backup_list.addItem(item)
        except Exception as e:
            item = QListWidgetItem(f"⚠️ Ошибка: {str(e)}")
            item.setFlags(Qt.NoItemFlags)
            self.backup_list.addItem(item)
        finally:
            db.close()

    def _on_selected(self, item: QListWidgetItem):
        path = item.data(Qt.UserRole)
        if not path:
            return
        self._selected_path = path
        p = Path(path)
        if p.exists():
            stat = p.stat()
            self.info_label.setText(
                f"Файл: {p.name}\n"
                f"Дата: {datetime.fromtimestamp(stat.st_mtime).strftime('%d.%m.%Y %H:%M')}\n"
                f"Размер: {stat.st_size / 1024 / 1024:.2f} MB\n"
                f"Путь: {path}"
            )
        self.restore_btn.setEnabled(True)
        self.del_btn.setEnabled(True)

    def _create_now(self):
        if QMessageBox.question(self, "Подтверждение",
                                "Создать резервную копию базы данных?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        self._show_progress("Создание резервной копии...")
        db = SessionLocal()
        try:
            svc = BackupService(db)
            path = svc.create_backup()
            self._hide_progress()
            QMessageBox.information(self, "Успех", f"Резервная копия создана:\n{path}")
            self._load_backups()
        except Exception as e:
            self._hide_progress()
            QMessageBox.warning(
                self, "Ошибка",
                f"Не удалось создать резервную копию:\n{str(e)}\n\n"
                f"Убедитесь, что pg_dump доступен в PATH."
            )
        finally:
            db.close()

    def _restore(self):
        if not self._selected_path:
            return
        reply = QMessageBox.question(
            self, "Подтверждение восстановления",
            "⚠️ ВНИМАНИЕ!\n\n"
            "Текущие данные будут заменены данными из резервной копии.\n"
            "Перед восстановлением автоматически создастся бэкап текущего состояния.\n\n"
            "Продолжить?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        self._show_progress("Восстановление данных...")
        self.restore_btn.setEnabled(False)
        db = SessionLocal()
        try:
            svc = BackupService(db)
            ok = svc.restore_backup(self._selected_path)
            self._hide_progress()
            if ok:
                QMessageBox.information(self, "Успех",
                                        "Данные успешно восстановлены!\n"
                                        "Пожалуйста, перезапустите приложение.")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось восстановить данные.")
        except Exception as e:
            self._hide_progress()
            QMessageBox.warning(self, "Ошибка восстановления", str(e))
        finally:
            db.close()
            self.restore_btn.setEnabled(True)

    def _delete_backup(self):
        if not self._selected_path:
            return
        if QMessageBox.question(self, "Удалить?",
                                "Удалить выбранную резервную копию?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            p = Path(self._selected_path)
            p.unlink(missing_ok=True)
            sha = p.with_suffix(".sql.sha256")
            if sha.exists():
                sha.unlink()
            self._load_backups()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def _show_progress(self, msg: str):
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(True)
        self.progress_lbl.setText(msg)
        self.progress_lbl.setVisible(True)

    def _hide_progress(self):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, lambda: (
            self.progress_bar.setVisible(False),
            self.progress_lbl.setVisible(False)
        ))
