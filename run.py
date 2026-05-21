#!/usr/bin/env python3
"""Единая точка запуска FocusGoal: инициализация БД + запуск GUI"""

import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Инициализация базы данных и справочников
def init_database():
    from src.config.database import init_db, SessionLocal
    from src.config.init_data import init_dictionary_data
    print("Инициализация базы данных...")
    init_db()
    db = SessionLocal()
    try:
        init_dictionary_data(db)
        print("Справочные данные загружены.")
    finally:
        db.close()

# Запуск GUI
def start_gui():
    from src.main import main
    main()

if __name__ == "__main__":
    # 1. Инициализируем БД
    init_database()
    # 2. Запускаем приложение
    start_gui()