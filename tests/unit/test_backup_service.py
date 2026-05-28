"""Тесты BackupService (ТЗ FR-010)"""
import pytest
import os
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.services.backup_service import BackupService


class TestBackupService:
    def test_checksum_calculation(self, tmp_path):
        """Проверка корректности sha256 контрольной суммы"""
        f = tmp_path / "test.sql"
        f.write_text("SELECT 1;")
        checksum = BackupService._checksum(str(f))
        expected = hashlib.sha256(b"SELECT 1;").hexdigest()
        assert checksum == expected

    def test_list_backups_empty(self, db_session, tmp_path, monkeypatch):
        """При пустой папке список пустой"""
        from src.config.settings import Settings
        monkeypatch.setattr(Settings, "BACKUP_DIR",
                            property(lambda self: tmp_path), raising=False)
        svc = BackupService(db_session)
        svc.settings.BACKUP_DIR = tmp_path
        result = svc.list_backups()
        assert result == []

    def test_list_backups_empty(self, db_session, tmp_path, monkeypatch):
        """При пустой папке список пустой"""
        from src.services.backup_service import BackupService
        # Временно подменяем атрибут BACKUP_DIR в объекте настроек
        svc = BackupService(db_session)
        # Используем monkeypatch для замены свойства на обычный атрибут
        monkeypatch.setattr(svc.settings, "BACKUP_DIR", tmp_path)
        result = svc.list_backups()
        assert result == []

    def test_restore_missing_file(self, db_session):
        """Восстановление несуществующего файла — FileNotFoundError"""
        svc = BackupService(db_session)
        with pytest.raises(FileNotFoundError):
            svc.restore_backup("/nonexistent/path/backup.sql")

    def test_restore_checksum_mismatch(self, db_session, tmp_path):
        """Повреждённый файл — ValueError"""
        f = tmp_path / "backup_20240101_120000.sql"
        f.write_text("corrupted data")
        sha = tmp_path / "backup_20240101_120000.sql.sha256"
        sha.write_text("wrongchecksum")
        svc = BackupService(db_session)
        with pytest.raises(ValueError, match="сумма"):
            svc.restore_backup(str(f))

    def test_cleanup_old_backups(self, db_session, tmp_path):
        """Очистка старых бэкапов — оставлять не более N"""
        for i in range(10):
            f = tmp_path / f"backup_2024010{i:02d}_000000.sql"
            f.write_text(f"-- backup {i}")
        svc = BackupService(db_session)
        svc.settings = MagicMock()
        svc.settings.BACKUP_DIR = tmp_path
        svc.settings.BACKUP_RETENTION_DAYS = 3
        svc.cleanup_old_backups()
        remaining = list(tmp_path.glob("backup_*.sql"))
        assert len(remaining) <= 3
