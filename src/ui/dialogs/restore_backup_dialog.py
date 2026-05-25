"""Диалог восстановления из резервной копии (ТЗ FR-010.2)"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QGroupBox, QMessageBox, QProgressBar, QFormLayout
)
from PyQt5.QtCore import Qt
from pathlib import Path
from datetime import datetime
from src.config.database import SessionLocal
from src.services.backup_service import BackupService


class RestoreBackupDialog(QDialog):
    def __init__(self, user_id: int = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self._selected = None
        self.setWindowTitle("Восстановление из резервной копии")
        self.setModal(True)
        self.setMinimumWidth(580)
        self.setMinimumHeight(500)
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("Восстановление данных")
        title.setProperty("role", "dialogTitle")
        layout.addWidget(title)

        warn = QLabel(
            "ВНИМАНИЕ! Текущие данные будут заменены данными из выбранной копии.\n"
            "Перед восстановлением автоматически создастся резервная копия текущего состояния."
        )
        warn.setProperty("role", "errorTextBold")
        warn.setWordWrap(True)
        layout.addWidget(warn)

        list_g = QGroupBox("Выберите резервную копию")
        ll = QVBoxLayout(list_g)
        self.backup_list = QListWidget()
        self.backup_list.setMinimumHeight(180)
        self.backup_list.itemClicked.connect(self._on_selected)
        ll.addWidget(self.backup_list)
        layout.addWidget(list_g)

        # Информация
        info_g = QGroupBox("Информация о копии")
        il = QFormLayout(info_g)
        self.info_lbl = QLabel("Выберите копию")
        self.info_lbl.setWordWrap(True)
        self.info_lbl.setProperty("role", "smallText")
        il.addRow(self.info_lbl)
        layout.addWidget(info_g)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setMinimumHeight(16)
        layout.addWidget(self.progress)

        btn_row = QHBoxLayout()
        self.restore_btn = QPushButton("Восстановить")
        self.restore_btn.setMinimumHeight(46)
        self.restore_btn.setObjectName("warningButton")
        self.restore_btn.setEnabled(False)
        self.restore_btn.clicked.connect(self._restore)
        btn_row.addWidget(self.restore_btn)

        refresh_btn = QPushButton("↻ Обновить")
        refresh_btn.setMinimumHeight(46)
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.clicked.connect(self._load)
        btn_row.addWidget(refresh_btn)

        cancel_btn = QPushButton("Закрыть")
        cancel_btn.setMinimumHeight(46)
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _load(self):
        self.backup_list.clear()
        self._selected = None
        self.restore_btn.setEnabled(False)
        db = SessionLocal()
        try:
            backups = BackupService(db).list_backups()
            if not backups:
                item = QListWidgetItem("📭 Резервных копий нет")
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
            item = QListWidgetItem(f"Ошибка: {str(e)}")
            item.setFlags(Qt.NoItemFlags)
            self.backup_list.addItem(item)
        finally:
            db.close()

    def _on_selected(self, item: QListWidgetItem):
        path = item.data(Qt.UserRole)
        if not path:
            return
        self._selected = path
        p = Path(path)
        if p.exists():
            stat = p.stat()
            self.info_lbl.setText(
                f"{p.name}\n"
                f"{datetime.fromtimestamp(stat.st_mtime).strftime('%d.%m.%Y %H:%M')}\n"
                f"{stat.st_size / 1024 / 1024:.2f} MB"
            )
        self.restore_btn.setEnabled(True)

    def _restore(self):
        if not self._selected:
            return
        if QMessageBox.question(
            self, "Подтвердите восстановление",
            "Все текущие данные будут заменены.\nПродолжить?",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        self.progress.setRange(0, 0)
        self.progress.setVisible(True)
        self.restore_btn.setEnabled(False)
        db = SessionLocal()
        try:
            ok = BackupService(db).restore_backup(self._selected)
            self.progress.setRange(0, 100)
            self.progress.setValue(100)
            if ok:
                QMessageBox.information(self, "Успех",
                    "Данные восстановлены! Перезапустите приложение.")
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Восстановление не удалось")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()
            self.progress.setVisible(False)
            self.restore_btn.setEnabled(True)
