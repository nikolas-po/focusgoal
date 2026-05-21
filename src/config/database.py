from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, scoped_session
from src.config.settings import Settings

settings = Settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
    pool_recycle=3600,
)

SessionLocal = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))

def init_db():
    from src.models.base import Base
    import src.models  # noqa
    Base.metadata.create_all(bind=engine)
    _repair_missing_timestamp_columns(engine)

def _repair_missing_timestamp_columns(engine):
    inspector = inspect(engine)
    with engine.begin() as conn:
        from src.models.base import Base
        for table_name in Base.metadata.tables.keys():
            if not inspector.has_table(table_name):
                continue
            columns = [c["name"] for c in inspector.get_columns(table_name)]
            if "created_at" not in columns:
                conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()'))
            if "updated_at" not in columns:
                conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()'))

def dispose_db():
    SessionLocal.remove()
    engine.dispose()