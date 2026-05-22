"""Сервис резервного копирования (ТЗ FR-010)"""
import subprocess
import os
import hashlib
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from src.config.settings import Settings


class BackupService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = Settings()
        self.settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    def create_backup(self, label: str = "") -> str:
        """Создать резервную копию БД через pg_dump"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{label}" if label else ""
        backup_file = self.settings.BACKUP_DIR / f"backup_{timestamp}{suffix}.sql"

        env = os.environ.copy()
        env["PGPASSWORD"] = self.settings.DB_PASSWORD

        cmd = [
            "pg_dump",
            "-h", self.settings.DB_HOST,
            "-p", str(self.settings.DB_PORT),
            "-U", self.settings.DB_USER,
            "-d", self.settings.DB_NAME,
            "--no-password",
            "-f", str(backup_file),
        ]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"pg_dump: {result.stderr}")

        # Контрольная сумма
        checksum = self._checksum(str(backup_file))
        backup_file.with_suffix(".sql.sha256").write_text(checksum)

        self.cleanup_old_backups()
        return str(backup_file)

    def restore_backup(self, backup_file: str) -> bool:
        """Восстановить БД из резервной копии"""
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise FileNotFoundError(f"Файл не найден: {backup_file}")

        sha_path = backup_path.with_suffix(".sql.sha256")
        if sha_path.exists():
            expected = sha_path.read_text().strip()
            actual = self._checksum(str(backup_path))
            if expected != actual:
                raise ValueError("Контрольная сумма не совпадает — файл повреждён")

        try:
            self.create_backup(label="before_restore")
        except Exception:
            pass

        env = os.environ.copy()
        env["PGPASSWORD"] = self.settings.DB_PASSWORD

        cmd = [
            "psql",
            "-h", self.settings.DB_HOST,
            "-p", str(self.settings.DB_PORT),
            "-U", self.settings.DB_USER,
            "-d", self.settings.DB_NAME,
            "--no-password",
            "-f", str(backup_file),
        ]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        return result.returncode == 0

    def list_backups(self) -> list:
        backups = sorted(
            self.settings.BACKUP_DIR.glob("backup_*.sql"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        result = []
        for f in backups[:20]:
            stat = f.stat()
            result.append({
                "path": str(f),
                "name": f.name,
                "date": datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
            })
        return result

    def cleanup_old_backups(self):
        backups = sorted(
            self.settings.BACKUP_DIR.glob("backup_*.sql"),
            key=lambda f: f.stat().st_mtime,
        )
        max_count = self.settings.BACKUP_RETENTION_DAYS
        for old in backups[:-max_count]:
            old.unlink(missing_ok=True)
            sha = old.with_suffix(".sql.sha256")
            if sha.exists():
                sha.unlink()

    @staticmethod
    def _checksum(file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
