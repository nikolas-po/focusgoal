"""Подключение к PostgreSQL через SQLAlchemy"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from src.config.settings import Settings

settings = Settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,      # автоматическая проверка соединения перед использованием
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
    pool_recycle=3600,
)

# scoped_session гарантирует отдельную сессию для каждого потока
SessionLocal = scoped_session(sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
))


def init_db():
    """Создать все таблицы БД и исправить схему, если в ней отсутствуют стандартные поля."""
    from src.models.base import Base
    import src.models  # noqa — регистрирует все модели через __init__.py
    Base.metadata.create_all(bind=engine)
    _repair_missing_timestamp_columns(engine)


def _repair_missing_timestamp_columns(engine):
    from sqlalchemy import inspect, text
    from src.models.base import Base

    inspector = inspect(engine)
    with engine.begin() as conn:
        for table_name in Base.metadata.tables.keys():
            if not inspector.has_table(table_name):
                continue
            columns = [column["name"] for column in inspector.get_columns(table_name)]
            for field in ("created_at", "updated_at"):
                if field not in columns:
                    conn.execute(text(
                        f'ALTER TABLE "{table_name}" ADD COLUMN "{field}" TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()'
                    ))


def dispose_db():
    """Закрыть все соединения и сбросить session pool"""
    SessionLocal.remove()
    engine.dispose()
