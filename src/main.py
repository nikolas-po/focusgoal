"""Точка входа FocusGoal"""
import argparse, os, signal, sys, shutil, tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
for p in (str(ROOT_DIR), str(Path.cwd())):
    if p not in sys.path:
        sys.path.insert(0, p)


def _setup_qt_env():
    if not os.environ.get("QT_QPA_PLATFORM"):
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            os.environ["QT_QPA_PLATFORM"] = "offscreen"
    if os.geteuid() == 0:
        rd = os.environ.get("XDG_RUNTIME_DIR", "")
        if not rd or not os.path.exists(rd):
            os.environ["XDG_RUNTIME_DIR"] = tempfile.mkdtemp(prefix="xdg-root-")
        os.environ.setdefault("QT_X11_NO_MITSHM", "1")

_setup_qt_env()

from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget, QPushButton, QToolButton
from PyQt5.QtGui import QPalette, QColor, QFont, QGuiApplication
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, QEvent
from src.config.settings import Settings
from src.config import theme_state

STYLES_DIR = Path(__file__).resolve().parent / "ui" / "styles"

#  Логгер 

def _logger():
    try:
        from src.config.logging_config import setup_logging
        return setup_logging()
    except Exception:
        import logging
        return logging.getLogger("FocusGoal")

#  Нормализация 

def _norm_theme(t: str) -> str:
    if t and t.strip().lower() in ("тёмная", "темная", "dark"):
        return "Тёмная"
    return "Светлая"

def _norm_font(v) -> int:
    if isinstance(v, int) and v in (12, 14, 16): return v
    m = {"маленький": 12, "средний": 14, "большой": 16,
         "12": 12, "14": 14, "16": 16,
         "12px": 12, "14px": 14, "16px": 16}
    return m.get(str(v).strip().lower(), 14)

def _hostname() -> str:
    import socket
    try: return socket.gethostname()
    except: return "default"

def supports_raise() -> bool:
    app = QApplication.instance()
    if not app: return False
    try: return QGuiApplication.platformName().lower() not in ("offscreen","minimal","minimalegl")
    except: return True

def safe_raise(w):
    if supports_raise():
        try: w.raise_(); w.activateWindow()
        except: pass

#  Стили 

def load_theme_style(theme: str, font_size: int = 14) -> str:
    tf = "dark_theme.qss" if theme == "Тёмная" else "light_theme.qss"
    parts = []
    for fn in ("common.qss", tf):
        try: parts.append((STYLES_DIR / fn).read_text(encoding="utf-8"))
        except Exception as e: _logger().warning(f"QSS {fn}: {e}")
    return "\n".join(parts).replace("{font_size}", str(font_size))


def apply_theme(theme: str, font_size: int):
    """Применить тему — быстро, без рекурсии по виджетам."""
    theme_state.current_theme = theme
    theme_state.current_font_size = font_size
    app = QApplication.instance()
    if not app: return
    style = load_theme_style(theme, font_size)
    app.setStyleSheet(style)
    app.setFont(QFont("Arial", font_size))
    _apply_palette(app, theme)
    # Перерисовать только верхние окна (достаточно для propagation)
    for w in app.topLevelWidgets():
        w.style().unpolish(w)
        w.style().polish(w)
        w.update()
        try:
            from src.ui.widgets.statistics_chart import StatisticsChart
            for chart in w.findChildren(StatisticsChart):
                chart.refresh_theme()
        except Exception:
            pass
    try:
        for widget in app.allWidgets():
            try:
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
            except Exception:
                pass
        app.processEvents()
    except Exception:
        pass
    try:
        for btn in app.findChildren(QPushButton):
            try:
                btn.setCursor(Qt.PointingHandCursor)
                obj_name = btn.objectName()
                if obj_name not in ("linkButton", "transparentButton"):
                    btn.setFlat(False)  
            except Exception:
                pass
    except Exception:
        pass
    _logger().info(f"Тема применена: {theme}, шрифт: {font_size}px")


def apply_saved_theme(app: QApplication, user_id: int = None):
    """Загрузить тему из БД и применить."""
    cur_host = _hostname()
    try:
        from src.config.database import SessionLocal
        from src.models.user import User
        db = SessionLocal()
        u = db.query(User).filter(User.id == user_id).first() if user_id else None
        if u and u.settings:
            saved_host = (u.settings or {}).get("hostname")
            if saved_host and saved_host != cur_host:
                _logger().info(f"Тема другого устройства ({saved_host}), по умолчанию")
                db.close()
                apply_theme(theme_state.current_theme, theme_state.current_font_size)
                return
            theme_state.current_theme = _norm_theme((u.settings or {}).get("theme", "Светлая"))
            theme_state.current_font_size = _norm_font((u.settings or {}).get("font_size", 14))
            _logger().info(f"Тема загружена: {theme_state.current_theme}, шрифт: {theme_state.current_font_size}px")
        db.close()
    except Exception as e:
        _logger().error(f"Ошибка загрузки темы: {e}")
    style = load_theme_style(theme_state.current_theme, theme_state.current_font_size)
    app.setStyleSheet(style)
    app.setFont(QFont("Arial", theme_state.current_font_size))
    _apply_palette(app, theme_state.current_theme)
    for w in app.topLevelWidgets():
        w.style().unpolish(w); w.style().polish(w); w.update()
        try:
            from src.ui.widgets.statistics_chart import StatisticsChart
            for chart in w.findChildren(StatisticsChart):
                chart.refresh_theme()
        except Exception:
            pass
    try:
        for widget in app.allWidgets():
            try:
                widget.style().unpolish(widget); widget.style().polish(widget); widget.update()
            except Exception:
                pass
        app.processEvents()
    except Exception:
        pass
    try:
        for btn in app.findChildren(QPushButton):
            try:
                btn.setCursor(Qt.PointingHandCursor)
                obj_name = btn.objectName()
                if obj_name not in ("linkButton", "transparentButton"):
                    btn.setFlat(False)  
            except Exception:
                pass
    except Exception:
        pass
    _logger().info("Сохранённая тема применена")


def save_user_theme(user_id: int, theme: str, font_size: int) -> bool:
    try:
        from src.config.database import SessionLocal
        from src.models.user import User
        db = SessionLocal()
        u = db.query(User).filter(User.id == user_id).first()
        if not u: db.close(); return False
        s = dict(u.settings or {})
        s.update({"theme": theme, "font_size": font_size, "hostname": _hostname()})
        u.settings = s
        db.commit(); db.close()
        _logger().info(f"Тема сохранена: {theme}, {font_size}px")
        return True
    except Exception as e:
        _logger().error(f"Сохранение темы: {e}"); return False


def _apply_palette(app, theme):
    p = QPalette()
    if theme == "Тёмная":
        p.setColor(QPalette.Window,          QColor(43,43,43))
        p.setColor(QPalette.WindowText,      QColor(224,224,224))
        p.setColor(QPalette.Base,            QColor(54,54,54))
        p.setColor(QPalette.AlternateBase,   QColor(66,66,66))
        p.setColor(QPalette.ToolTipBase,     QColor(255,255,255))
        p.setColor(QPalette.ToolTipText,     QColor(33,33,33))
        p.setColor(QPalette.Text,            QColor(224,224,224))
        p.setColor(QPalette.Button,          QColor(58,58,58))
        p.setColor(QPalette.ButtonText,      QColor(224,224,224))
        p.setColor(QPalette.Highlight,       QColor(76,175,80))
        p.setColor(QPalette.HighlightedText, QColor(0,0,0))
        p.setColor(QPalette.Link,            QColor(33,150,243))
        p.setColor(QPalette.Mid,             QColor(80,80,80))
        p.setColor(QPalette.Dark,            QColor(35,35,35))
    else:
        p.setColor(QPalette.Window,          QColor(245,245,245))
        p.setColor(QPalette.WindowText,      QColor(33,33,33))
        p.setColor(QPalette.Base,            QColor(255,255,255))
        p.setColor(QPalette.AlternateBase,   QColor(240,240,240))
        p.setColor(QPalette.ToolTipBase,     QColor(255,255,255))
        p.setColor(QPalette.ToolTipText,     QColor(33,33,33))
        p.setColor(QPalette.Text,            QColor(33,33,33))
        p.setColor(QPalette.Button,          QColor(240,240,240))
        p.setColor(QPalette.ButtonText,      QColor(33,33,33))
        p.setColor(QPalette.Highlight,       QColor(76,175,80))
        p.setColor(QPalette.HighlightedText, QColor(255,255,255))
        p.setColor(QPalette.Link,            QColor(33,150,243))
        p.setColor(QPalette.Mid,             QColor(180,180,180))
        p.setColor(QPalette.Dark,            QColor(160,160,160))
    app.setPalette(p)

#  Инициализация 

def _init_app(logger) -> Settings:
    logger.info("Инициализация приложения")
    s = Settings(); s.create_directories()
    try:
        free = shutil.disk_usage(s.BASE_DIR).free // (1024*1024)
        if free < s.MIN_DISK_SPACE_MB:
            QMessageBox.warning(None,"Мало места",f"Свободно: {free} МБ")
    except: pass
    logger.info("Приложение инициализировано")
    return s


class _ButtonMonitor(QObject):
    def __init__(self, app):
        super().__init__(app)
        self._app = app

    def eventFilter(self, obj, event):
        try:
            if event.type() == QEvent.ChildAdded:
                if hasattr(event, 'child'):
                    try:
                        ch = event.child()
                    except Exception:
                        ch = None
                    if isinstance(ch, QPushButton):
                        self._fix_button(ch)
            if event.type() == QEvent.Show and isinstance(obj, QPushButton):
                self._fix_button(obj)
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def _fix_button(self, btn: QPushButton):
        try:
            try: btn.setCursor(Qt.PointingHandCursor)
            except: pass
            obj_name = btn.objectName()
            if obj_name in ("linkButton", "transparentButton"):
                btn.setFlat(True)
            else:
                btn.setFlat(False) 
        except Exception:
            pass


def _init_db(logger) -> bool:
    logger.info("Инициализация БД")
    try:
        from src.config.database import init_db, SessionLocal
        from src.config.init_data import init_dictionary_data
        init_db()
        db = SessionLocal()
        try: init_dictionary_data(db)
        except: db.rollback(); raise
        finally: db.close(); SessionLocal.remove()
        logger.info("БД инициализирована"); return True
    except Exception as e:
        logger.error(f"БД ошибка: {e}")
        QMessageBox.critical(None,"Ошибка БД",
            f"PostgreSQL недоступен.\n\n"
            f"1. Проверьте что PostgreSQL запущен\n"
            f"2. Параметры в .env верны\n\nОшибка: {e}")
        return False


def _start_scheduler(settings: Settings, logger):
    logger.info("Запуск планировщика задач")
    try:
        from src.services.notification_service import NotificationService
        from src.config.database import SessionLocal
        NotificationService.start_scheduler()
        parts = settings.AUTO_BACKUP_TIME.split(":")
        db = SessionLocal()
        notif_service = NotificationService(db)
        notif_service.schedule_daily_backup(int(parts[0]), int(parts[1]))
        notif_service.schedule_notifications(interval_minutes=1)  # Проверять каждую минуту для напоминаний
        db.close()
        logger.info("Планировщик запущен")
    except Exception as e:
        logger.warning(f"Планировщик: {e}")


def _try_autologin(settings: Settings, logger):
    f = settings.BASE_DIR / ".focusgoal_remember.json"
    if not f.exists(): return None
    try:
        import json
        from src.utils.encryption import decrypt_bytes
        raw = f.read_bytes()
        if settings.ENCRYPTION_KEY:
            try: raw = decrypt_bytes(raw, settings.ENCRYPTION_KEY)
            except: pass
        d = json.loads(raw.decode())
        nick, pwd = d.get("nickname",""), d.get("password","")
        if not nick or not pwd: return None
        from src.config.database import SessionLocal
        from src.services.auth_service import AuthService
        db = SessionLocal()
        try:
            ud = AuthService(db).login(nick, pwd)
            logger.info(f"Автовход: {nick} (ID={ud['id']})")
            return ud
        except Exception as e:
            logger.warning(f"Автовход не удался: {e}"); return None
        finally: db.close()
    except Exception as e:
        logger.warning(f"Remember-файл: {e}"); return None


def _show_window(app, user_data, settings, logger):
    if user_data:
        logger.info(f"Главное окно: {user_data.get('nickname')}")
        from src.ui.windows.main_window import MainWindow
        win = MainWindow(user_data)
        apply_saved_theme(app, user_data["id"])
    else:
        logger.info("Окно входа")
        from src.ui.windows.login_window import LoginWindow
        win = LoginWindow(settings)
        apply_theme(theme_state.current_theme, theme_state.current_font_size)
    win.show(); safe_raise(win)
    return win


def _fetch_user(uid: int):
    try:
        from src.config.database import SessionLocal
        from src.models.user import User
        db = SessionLocal()
        u = db.query(User).filter(User.id == uid).first()
        if u: return {"id": u.id, "nickname": u.nickname, "timezone": u.timezone}
    except: pass
    finally:
        try: db.close()
        except: pass
    return None


def _parse_args():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--resume-user",       type=int)
    p.add_argument("--resume-focus",      action="store_true")
    p.add_argument("--resume-duration",   type=int, default=25)
    p.add_argument("--resume-block-level",type=int, default=1)
    p.add_argument("--close-pid",         type=int, default=0)
    args, _ = p.parse_known_args()
    return args

#  Точка входа 

def main():
    args = _parse_args()

    # Закрыть предыдущий процесс (при перезапуске с правами root)
    if args.close_pid:
        try:
            import psutil
            parent = psutil.Process(args.close_pid)
            parent.terminate()
            parent.wait(timeout=3)
        except Exception:
            pass

    # SetAttributes ДОЛЖНЫ быть ДО QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    try:
        app = QApplication(sys.argv)
    except Exception as e:
        print(f"Qt init error: {e}"); sys.exit(1)

    from PyQt5.QtWidgets import QStyleFactory
    available_styles = QStyleFactory.keys()
    style_to_use = "Fusion"  # Default to Fusion
    for preferred in ["Plastique", "Cleanlooks", "GTK+", "Oxygen"]:
        if preferred in available_styles:
            style_to_use = preferred
            break
    app.setStyle(style_to_use)
    app.setApplicationName("FocusGoal")
    app.setOrganizationName("FocusGoal")

    try:
        monitor = _ButtonMonitor(app)
        app.installEventFilter(monitor)
    except Exception:
        pass

    # Обработка Ctrl+C — корректная остановка планировщика и Qt
    def _sigint(*_):
        _logger().info("SIGINT — завершение")
        _shutdown()
        app.quit()

    def _shutdown():
        try:
            from src.services.notification_service import NotificationService
            NotificationService.stop_scheduler()
        except: pass

    signal.signal(signal.SIGINT, _sigint)
    signal.signal(signal.SIGTERM, _sigint)

    logger = _logger()
    logger.info("Запуск FocusGoal")

    settings = _init_app(logger)
    if not _init_db(logger): sys.exit(1)
    _start_scheduler(settings, logger)

    user_data = _fetch_user(args.resume_user) if args.resume_user else None
    if not user_data:
        user_data = _try_autologin(settings, logger)

    win = _show_window(app, user_data, settings, logger)

    if user_data and args.resume_focus and hasattr(win, "start_focus_session"):
        win.start_focus_session(args.resume_duration, args.resume_block_level)

    logger.info("Приложение готово")
    ret = app.exec_()
    _shutdown()
    logger.info(f"Завершение работы (код {ret})")
    sys.exit(ret)


if __name__ == "__main__":
    main()
