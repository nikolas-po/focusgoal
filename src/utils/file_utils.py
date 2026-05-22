"""Утилиты для работы с файлами"""
import os
import shutil
from pathlib import Path
from datetime import datetime


def ensure_dir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_file_size_mb(path: str) -> float:
    try:
        return round(os.path.getsize(path) / 1024 / 1024, 2)
    except OSError:
        return 0.0


def safe_delete(path: str) -> bool:
    try:
        p = Path(path)
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)
        return True
    except Exception:
        return False


def generate_filename(prefix: str, extension: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{extension}"
