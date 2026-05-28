"""003 drop gdpr_consent from user table

Revision ID: 003
Revises: 002
Create Date: 2025-06-01 00:00:00.000000

Удаляет поле gdpr_consent из таблицы user.
Поле было добавлено в ревизии 001 и должно быть убрано:
  - приложение не передаёт данные третьим лицам,
  - данные хранятся исключительно локально на устройстве пользователя,
  - сбор согласия по внешним регуляторным требованиям не требуется.

Для баз данных созданных после исправления 001 — миграция будет
выполнена безопасно (IF EXISTS / checkfirst).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    """Проверить наличие столбца перед удалением (idempotent upgrade)."""
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def upgrade():
    """Удалить gdpr_consent если столбец существует."""
    if _column_exists("user", "gdpr_consent"):
        op.drop_column("user", "gdpr_consent")


def downgrade():
    """Восстановить gdpr_consent (nullable, без ограничений)."""
    if not _column_exists("user", "gdpr_consent"):
        op.add_column(
            "user",
            sa.Column("gdpr_consent", sa.DateTime, nullable=True),
        )
