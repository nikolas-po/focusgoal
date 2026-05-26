"""Окно статистики (ТЗ FR-005, FR-007)"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QComboBox, QScrollArea,
    QGridLayout, QFrame, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from src.ui.widgets.statistics_chart import StatisticsChart
from src.ui.widgets.heatmap import HabitHeatmap
from src.config.database import SessionLocal
from src.services.statistics_service import StatisticsService


class StatisticsWindow(QWidget):
    def __init__(self, user_id: int = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(18)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("Статистика и аналитика")
        title.setProperty("role", "pageTitle")
        layout.addWidget(title)

        # Панель управления
        ctrl = QHBoxLayout()
        period_g = QGroupBox("Период")
        pg_l = QHBoxLayout(period_g)
        pg_l.addWidget(QLabel("За:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["7 дней", "30 дней", "90 дней", "Год"])
        self.period_combo.setCurrentIndex(1)
        self.period_combo.setMinimumHeight(36)
        pg_l.addWidget(self.period_combo)
        upd_btn = QPushButton("Обновить")
        upd_btn.setMinimumHeight(36)
        upd_btn.setObjectName("secondaryButton")
        upd_btn.clicked.connect(self._load_statistics)
        pg_l.addWidget(upd_btn)
        ctrl.addWidget(period_g)

        exp_g = QGroupBox("Экспорт")
        eg_l = QHBoxLayout(exp_g)
        pdf_btn = QPushButton("PDF")
        pdf_btn.setMinimumHeight(36)
        pdf_btn.setObjectName("secondaryButton")
        pdf_btn.clicked.connect(self._export_pdf)
        csv_btn = QPushButton("CSV")
        csv_btn.setMinimumHeight(36)
        csv_btn.setObjectName("secondaryButton")
        csv_btn.clicked.connect(self._export_csv)
        json_btn = QPushButton("JSON")
        json_btn.setMinimumHeight(36)
        json_btn.setObjectName("secondaryButton")
        json_btn.clicked.connect(self._export_json)
        for b in [pdf_btn, csv_btn, json_btn]:
            eg_l.addWidget(b)
        ctrl.addWidget(exp_g)
        layout.addLayout(ctrl)

        # Карточки сводки
        sg = QGroupBox("Сводная статистика")
        sg_l = QGridLayout(sg)
        sg_l.setSpacing(12)
        self.goals_card  = self._card("Выполнено целей", "0")
        self.habits_card = self._card("Активных привычек", "0")
        self.focus_card  = self._card("Время в фокусе", "0ч")
        self.prod_card   = self._card("Продуктивность", "0%")
        sg_l.addWidget(self.goals_card,  0, 0)
        sg_l.addWidget(self.habits_card, 0, 1)
        sg_l.addWidget(self.focus_card,  1, 0)
        sg_l.addWidget(self.prod_card,   1, 1)
        layout.addWidget(sg)

        # Графики
        cg = QGroupBox("Визуализация")
        cg_l = QVBoxLayout(cg)
        for attr, label in [
            ("goals_chart",  "Цели по дням:"),
            ("habits_chart", "Привычки по дням:"),
            ("focus_chart",  "Статус фокус-сессий:"),
        ]:
            lbl = QLabel(label)
            lbl.setProperty("role", "boldText")
            cg_l.addWidget(lbl)
            chart = StatisticsChart()
            chart.setMinimumHeight(230)
            setattr(self, attr, chart)
            cg_l.addWidget(chart)
        layout.addWidget(cg)

        # Тепловая карта
        hm_g = QGroupBox("Тепловая карта привычек (12 недель)")
        hm_l = QVBoxLayout(hm_g)
        self.heatmap = HabitHeatmap()
        hm_l.addWidget(self.heatmap)
        layout.addWidget(hm_g)

        container.setLayout(layout)
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def _card(self, title: str, value: str) -> QFrame:
        f = QFrame()
        f.setObjectName("statCard")
        f.setMinimumHeight(100)
        cl = QVBoxLayout(f)
        cl.setContentsMargins(15, 12, 15, 12)
        tl = QLabel(title)
        tl.setProperty("role", "mutedSmallText")
        cl.addWidget(tl)
        vl = QLabel(value)
        vl.setObjectName("valueLabel")
        vl.setProperty("role", "bigValueLabel")
        cl.addWidget(vl)
        return f

    def _update_card(self, card: QFrame, value: str):
        for lbl in card.findChildren(QLabel):
            if lbl.objectName() == "valueLabel":
                lbl.setText(value)

    def _load_statistics(self):
        if not self.user_id:
            return
        from PyQt5.QtWidgets import QApplication
        QApplication.setOverrideCursor(__import__('PyQt5.QtCore', fromlist=['Qt']).Qt.WaitCursor)
        try:
            self._do_load_statistics()
        finally:
            QApplication.restoreOverrideCursor()

    def _do_load_statistics(self):
        if not self.user_id:
            return
        period_map = {0: 7, 1: 30, 2: 90, 3: 365}
        days = period_map.get(self.period_combo.currentIndex(), 30)

        db = SessionLocal()
        try:
            svc = StatisticsService(db)
            st = svc.get_dashboard_statistics(self.user_id)

            self._update_card(self.goals_card,  str(st["goals"]["completed"]))
            self._update_card(self.habits_card, str(st["habits"]["active"]))
            h = st["focus"]["total_minutes"] // 60
            m = st["focus"]["total_minutes"] % 60
            self._update_card(self.focus_card, f"{h}ч {m}м")
            self._update_card(self.prod_card, f"{st['goals']['rate']:.0f}%")

            gd = svc.get_goals_by_period(self.user_id, days)
            if gd:
                self.goals_chart.plot_bar_chart(
                    [d["date"][-5:] for d in gd[-14:]],
                    [d["count"] for d in gd[-14:]],
                    f"Цели за {days} дн."
                )
            else:
                self.goals_chart.plot_bar_chart([], [], "Нет данных о целях")

            hd = svc.get_habits_by_period(self.user_id, days)
            if hd:
                self.habits_chart.plot_line_chart(
                    [d["date"][-5:] for d in hd[-14:]],
                    [d["count"] for d in hd[-14:]],
                    f"Привычки за {days} дн."
                )
            else:
                self.habits_chart.plot_line_chart([], [], "Нет данных о привычках")

            fd = svc.get_focus_status_distribution(self.user_id)
            if sum(fd.values()) > 0:
                self.focus_chart.plot_pie_chart(
                    ["Завершено", "Прервано", "Прервано внешне"],
                    [fd["completed"], fd["cancelled"], fd["interrupted"]],
                    "Статус фокус-сессий"
                )
            else:
                self.focus_chart.plot_pie_chart(["Нет сессий"], [1], "Фокус")

            self.heatmap.update_data(svc.get_heatmap_data(self.user_id))
        except Exception:
            pass
        finally:
            db.close()

    def _export_pdf(self):
        from pathlib import Path
        from datetime import datetime
        opts = QFileDialog.Options()
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить PDF",
            str(Path.home() / "Downloads" /
                f"focusgoal_{datetime.now().strftime('%Y%m%d')}.pdf"),
            "PDF (*.pdf)", options=opts
        )
        if not path: return
        db = SessionLocal()
        try:
            from src.services.export_service import ExportService
            ExportService(db, self.user_id).export_to_pdf(path)
            QMessageBox.information(self, "Успех", f"PDF сохранён:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()

    def _export_csv(self):
        from pathlib import Path
        from datetime import datetime
        opts = QFileDialog.Options()
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить CSV",
            str(Path.home() / "Downloads" /
                f"focusgoal_{datetime.now().strftime('%Y%m%d')}.csv"),
            "CSV (*.csv)", options=opts
        )
        if not path: return
        db = SessionLocal()
        try:
            from src.services.export_service import ExportService
            ExportService(db, self.user_id).export_to_csv(path)
            QMessageBox.information(self, "Успех", f"CSV сохранён:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()

    def _export_json(self):
        from pathlib import Path
        from datetime import datetime
        opts = QFileDialog.Options()
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить JSON",
            str(Path.home() / "Downloads" /
                f"focusgoal_{datetime.now().strftime('%Y%m%d')}.json"),
            "JSON (*.json)", options=opts
        )
        if not path: return
        db = SessionLocal()
        try:
            from src.services.export_service import ExportService
            ExportService(db, self.user_id).export_to_json(path, encrypt=False)
            QMessageBox.information(self, "Успех", f"JSON сохранён:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        finally:
            db.close()
