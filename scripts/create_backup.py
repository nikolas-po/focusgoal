#!/usr/bin/env python3
"""Скрипт ручного создания резервной копии"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database import SessionLocal
from src.services.backup_service import BackupService

if __name__ == "__main__":
    label = sys.argv[1] if len(sys.argv) > 1 else "manual"
    db = SessionLocal()
    try:
        svc = BackupService(db)
        path = svc.create_backup(label=label)
        print(f"OK: {path}")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        db.close()
