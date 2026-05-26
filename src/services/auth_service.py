"""Сервис аутентификации (ТЗ FR-001, безопасность, 152-ФЗ)"""
import bcrypt
from sqlalchemy.orm import Session
from src.repositories.user_repository import UserRepository
from src.models.user import User
from src.config.settings import Settings
from typing import Dict
from datetime import datetime, timezone, timedelta


class AuthService:
    def __init__(self, db: Session):
        self.db        = db
        self.user_repo = UserRepository(db)
        self.settings  = Settings()
        self._failed: Dict[str, list] = {}

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def validate_password(self, password: str) -> tuple:
        if len(password) < self.settings.PASSWORD_MIN_LENGTH:
            return False, f"Пароль минимум {self.settings.PASSWORD_MIN_LENGTH} символов"
        if not any(c.isalpha() for c in password):
            return False, "Пароль должен содержать буквы"
        if not any(c.isdigit() for c in password):
            return False, "Пароль должен содержать цифры"
        return True, ""

    def validate_nickname(self, nickname: str) -> tuple:
        n = nickname.strip()
        if len(n) < self.settings.NICKNAME_MIN_LENGTH:
            return False, f"Никнейм минимум {self.settings.NICKNAME_MIN_LENGTH} символа"
        if len(n) > self.settings.NICKNAME_MAX_LENGTH:
            return False, f"Никнейм максимум {self.settings.NICKNAME_MAX_LENGTH} символов"
        if self.user_repo.nickname_exists(n):
            return False, "Этот никнейм уже занят"
        return True, ""

    def register(self, nickname: str, password: str,
                 email: str = None, timezone_name: str = "Europe/Moscow") -> Dict:
        """Регистрация пользователя"""
        ok, err = self.validate_nickname(nickname)
        if not ok: raise ValueError(err)
        ok, err = self.validate_password(password)
        if not ok: raise ValueError(err)
        if email and self.user_repo.email_exists(email):
            raise ValueError("Email уже зарегистрирован")

        now_local = datetime.now()

        user = self.user_repo.create(
            nickname=nickname.strip(),
            email=email or None,
            password_hash=self.hash_password(password),
            timezone=timezone_name,
            settings={},
        )
        return {
            "id": user.id,
            "nickname": user.nickname,
            "registered_at": user.registered_at.isoformat(),
        }

    def login(self, nickname: str, password: str) -> Dict:
        if self._is_blocked(nickname):
            raise ValueError(
                f"Вход заблокирован. Подождите {self.settings.LOGIN_BLOCK_TIME} сек."
            )
        user = self.user_repo.get_by_nickname(nickname)
        if not user:
            self._record_fail(nickname)
            raise ValueError("Пользователь не найден")
        if not self.verify_password(password, user.password_hash):
            self._record_fail(nickname)
            attempts, _ = self._failed.get(nickname, [0, None])
            left = self.settings.MAX_LOGIN_ATTEMPTS - attempts
            if left > 0:
                raise ValueError(f"Неверный пароль. Осталось попыток: {left}")
            raise ValueError("Неверный пароль. Вход заблокирован на 30 секунд")
        self._failed.pop(nickname, None)
        return {"id": user.id, "nickname": user.nickname, "timezone": user.timezone}

    def change_password(self, user_id: int, new_password: str) -> bool:
        ok, err = self.validate_password(new_password)
        if not ok: raise ValueError(err)
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user: raise ValueError("Пользователь не найден")
        user.password_hash = self.hash_password(new_password)
        self.db.commit()
        return True

    def delete_user_data(self, user_id: int) -> bool:
        """Немедленное удаление аккаунта и всех связанных данных"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        try:
            # Удаляем пользователя; каскадное удаление настроено через FK
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def _is_blocked(self, nick: str) -> bool:
        if nick not in self._failed: return False
        attempts, until = self._failed[nick]
        if attempts >= self.settings.MAX_LOGIN_ATTEMPTS:
            if datetime.now() < until: return True
            self._failed.pop(nick, None)
        return False

    def _record_fail(self, nick: str):
        if nick not in self._failed:
            self._failed[nick] = [0, datetime.now()]
        self._failed[nick][0] += 1
        if self._failed[nick][0] >= self.settings.MAX_LOGIN_ATTEMPTS:
            self._failed[nick][1] = (
                datetime.now() + timedelta(seconds=self.settings.LOGIN_BLOCK_TIME)
            )
