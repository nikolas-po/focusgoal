"""Базовый репозиторий с CRUD и автовосстановлением сессии"""
from typing import TypeVar, Generic, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import InvalidRequestError
from src.models.base import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    def __init__(self, model: type, db: Session):
        self.model = model
        self.db    = db

    def _safe_query(self):
        """Откат сломанной транзакции перед выполнением запроса"""
        try:
            # Проверяем состояние соединения
            self.db.execute("SELECT 1")
        except Exception:
            try:
                self.db.rollback()
            except Exception:
                pass
        return self.db.query(self.model)

    def create(self, **kwargs) -> T:
        obj = self.model(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, id: int) -> Optional[T]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def update(self, id: int, **kwargs) -> Optional[T]:
        obj = self.get_by_id(id)
        if obj:
            for k, v in kwargs.items():
                if hasattr(obj, k):
                    setattr(obj, k, v)
            self.db.commit()
            self.db.refresh(obj)
        return obj

    def delete(self, id: int) -> bool:
        obj = self.get_by_id(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False
