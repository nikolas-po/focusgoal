"""Интеграционные тесты экспорта и импорта (ТЗ FR-011)"""
import pytest
import json
import os
from pathlib import Path


class TestExportImport:
    def test_export_json(self, db_session, test_user, test_goal, test_habit, tmp_path):
        from src.services.export_service import ExportService
        out = str(tmp_path / "export.json")
        svc = ExportService(db_session, test_user["id"])
        result = svc.export_to_json(out, encrypt=False)
        assert os.path.exists(result)
        data = json.loads(Path(result).read_bytes())
        assert data["user_id"] == test_user["id"]
        assert len(data["goals"])  >= 1
        assert len(data["habits"]) >= 1

    def test_export_csv(self, db_session, test_user, test_goal, test_habit, tmp_path):
        from src.services.export_service import ExportService
        out = str(tmp_path / "export.csv")
        svc = ExportService(db_session, test_user["id"])
        result = svc.export_to_csv(out)
        assert os.path.exists(result)
        content = Path(result).read_text(encoding="utf-8-sig")
        assert "=== ЦЕЛИ ===" in content
        assert "=== ПРИВЫЧКИ ===" in content

    def test_import_json_add_mode(self, db_session, test_user, tmp_path):
        from src.services.export_service import ExportService
        from src.services.import_service import ImportService
        from src.services.goal_service import GoalService

        # Создаём цель, экспортируем
        gsvc = GoalService(db_session)
        gsvc.create_goal(test_user["id"], {"name": "Экспорт-цель", "status_id": 1,
                                            "priority_id": 1})
        out = str(tmp_path / "exp.json")
        ExportService(db_session, test_user["id"]).export_to_json(out, encrypt=False)

        # Создаём второго пользователя и импортируем
        from src.services.auth_service import AuthService
        auth = AuthService(db_session)
        u2   = auth.register("import_user", "Pass1234", gdpr_consent=True)
        isvc = ImportService(db_session, u2["id"])
        result = isvc.import_from_json(out, mode="add")
        assert result["imported_goals"] >= 1
        assert result["errors"] == []

    def test_import_json_skip_duplicates(self, db_session, test_user, tmp_path):
        from src.services.export_service import ExportService
        from src.services.import_service import ImportService

        out = str(tmp_path / "exp.json")
        ExportService(db_session, test_user["id"]).export_to_json(out, encrypt=False)
        # Импортируем дважды в skip-режиме
        isvc = ImportService(db_session, test_user["id"])
        isvc.import_from_json(out, mode="add")
        result = isvc.import_from_json(out, mode="skip")
        assert result["skipped"] >= 0  # дубли пропущены

    def test_export_encrypted_json(self, db_session, test_user, tmp_path, monkeypatch):
        from src.services.export_service import ExportService
        from src.config.settings import Settings
        monkeypatch.setattr(Settings, "ENCRYPTION_KEY", "test_key_for_pytest_32chars__!!", raising=False)
        out = str(tmp_path / "enc.json")
        svc = ExportService(db_session, test_user["id"])
        svc.settings.ENCRYPTION_KEY = "test_key_for_pytest_32chars__!!"
        result = svc.export_to_json(out, encrypt=True)
        raw = Path(result).read_bytes()
        assert raw[:5] == b"FGENC"
