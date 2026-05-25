"""Тесты AuthService (ТЗ FR-001)"""
import pytest
from src.services.auth_service import AuthService


class TestAuthService:
    def test_register_success(self, db_session):
        auth = AuthService(db_session)
        result = auth.register("newuser1", "Pass1234")
        assert result["id"] is not None
        assert result["nickname"] == "newuser1"

    def test_register_duplicate_nickname(self, db_session, test_user):
        auth = AuthService(db_session)
        with pytest.raises(ValueError, match="уже занят"):
            auth.register("testuser", "Pass1234")

    def test_register_short_nickname(self, db_session):
        auth = AuthService(db_session)
        with pytest.raises(ValueError):
            auth.register("ab", "Pass1234")

    def test_register_weak_password(self, db_session):
        auth = AuthService(db_session)
        with pytest.raises(ValueError):
            auth.register("validnick2", "short")

    def test_register_password_no_digit(self, db_session):
        auth = AuthService(db_session)
        with pytest.raises(ValueError, match="цифры"):
            auth.register("validnick3", "NoDigitsHere")

    def test_register_password_no_letter(self, db_session):
        auth = AuthService(db_session)
        with pytest.raises(ValueError, match="буквы"):
            auth.register("validnick4", "12345678")

    def test_login_success(self, db_session, test_user):
        auth = AuthService(db_session)
        result = auth.login("testuser", "Password123")
        assert result["id"] == test_user["id"]
        assert result["nickname"] == "testuser"

    def test_login_wrong_password(self, db_session, test_user):
        auth = AuthService(db_session)
        with pytest.raises(ValueError, match="Неверный"):
            auth.login("testuser", "WrongPassword1")

    def test_login_user_not_found(self, db_session):
        auth = AuthService(db_session)
        with pytest.raises(ValueError, match="не найден"):
            auth.login("nonexistent", "Pass1234")

    def test_hash_password(self, db_session):
        auth = AuthService(db_session)
        hashed = auth.hash_password("Password123")
        assert hashed != "Password123"
        assert auth.verify_password("Password123", hashed)

    def test_change_password(self, db_session, test_user):
        auth = AuthService(db_session)
        result = auth.change_password(test_user["id"], "NewPass456")
        assert result is True
        login = auth.login("testuser", "NewPass456")
        assert login["id"] == test_user["id"]

    def test_login_blocking(self, db_session):
        auth = AuthService(db_session)
        auth.register("blocktest", "Pass1234")
        for _ in range(5):
            try:
                auth.login("blocktest", "WrongPassword1")
            except ValueError:
                pass
        with pytest.raises(ValueError, match="заблокирован"):
            auth.login("blocktest", "WrongPassword1")
