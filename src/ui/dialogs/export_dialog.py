"""Диалог экспорта (ТЗ FR-011) — JSON/CSV/Excel/PDF"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QRadioButton, QButtonGroup, QCheckBox,
    QFileDialog, QMessageBox, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt
from pathlib import Path
from datetime import datetime
from src.config.database import SessionLocal
from src.services.export_service import ExportService

class ExportDialog(QDialog):
    def __init__(self, user_id=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Экспорт данных")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setMinimumHeight(500)
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(14); layout.setContentsMargins(25,25,25,25)

        title = QLabel("Экспорт данных")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        fmt_g = QGroupBox("Формат экспорта")
        fl = QVBoxLayout(fmt_g)
        self.fmt_group = QButtonGroup()
        for fid, label in [
            (1, "JSON — полный экспорт (шифрование AES-256)"),
            (2, "CSV  — таблицы для внешних систем"),
            (3, "Excel (.xlsx) — форматированная таблица"),
            (4, "PDF  — отчёт для печати"),
        ]:
            rb = QRadioButton(label)
            self.fmt_group.addButton(rb, fid)
            fl.addWidget(rb)
            if fid == 1: rb.setChecked(True)
        layout.addWidget(fmt_g)

        self.json_opts = QGroupBox("Параметры JSON")
        jl = QVBoxLayout(self.json_opts)
        self.encrypt_check = QCheckBox("Шифровать файл (AES-256, ключ из .env)")
        self.encrypt_check.setChecked(True)
        jl.addWidget(self.encrypt_check)
        layout.addWidget(self.json_opts)
        self.fmt_group.buttonClicked.connect(
            lambda: self.json_opts.setVisible(self.fmt_group.checkedId() == 1))
        layout.addStretch()

        btn_row = QHBoxLayout()
        exp_btn = QPushButton("Экспортировать"); exp_btn.setMinimumHeight(48)
        exp_btn.clicked.connect(self._export); btn_row.addWidget(exp_btn)
        cancel_btn = QPushButton("Отмена"); cancel_btn.setMinimumHeight(48)
        cancel_btn.setObjectName("cancelButton"); cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        container.setLayout(layout); scroll.setWidget(container)
        outer = QVBoxLayout(self); outer.addWidget(scroll)
        self.setStyleSheet("""
            QDialog { background: palette(window); color: palette(windowText); }
            QGroupBox { font-weight:bold; border:1px solid palette(mid); border-radius:8px; margin-top:8px; padding-top:12px; }
            QGroupBox::title { subcontrol-origin:margin; left:10px; padding:0 4px; }
            QPushButton { background: palette(button); color: palette(buttonText); border:none; border-radius:4px; font-weight:bold; font-size:14px; }
            QPushButton:hover { background: palette(highlight); }
            QPushButton#cancelButton { background: palette(mid); color: palette(windowText); }
        """)

    def _export(self):
        fmt = self.fmt_group.checkedId()
        ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext_map = {
            1:("JSON Files (*.json)", f"focusgoal_{ts}.json"),
            2:("CSV Files (*.csv)",   f"focusgoal_{ts}.csv"),
            3:("Excel Files (*.xlsx)",f"focusgoal_{ts}.xlsx"),
            4:("PDF Files (*.pdf)",   f"focusgoal_{ts}.pdf"),
        }
        fstr, fname = ext_map[fmt]
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить", str(Path.home()/"Downloads"/fname), fstr)
        if not path: return
        db = SessionLocal()
        try:
            svc = ExportService(db, self.user_id)
            {1: lambda: svc.export_to_json(path, self.encrypt_check.isChecked()),
             2: lambda: svc.export_to_csv(path),
             3: lambda: svc.export_to_xlsx(path),
             4: lambda: svc.export_to_pdf(path)}[fmt]()
            QMessageBox.information(self, "Успех", f"Сохранено:\n{path}")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()
