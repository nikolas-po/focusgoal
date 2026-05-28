"""002 remove gdpr_consent placeholder

Revision ID: 002
Revises: 001
Create Date: 2025-05-09 00:00:00.000000

Эта миграция изначально добавляла поле gdpr_consent (сбор согласия
по 152-ФЗ). Поле убрано из проекта — данные хранятся локально,
обработки персональных данных третьими лицами нет.
Миграция оставлена как no-op для сохранения цепочки ревизий.
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # no-op: поле gdpr_consent было удалено из схемы до применения 001
    pass


def downgrade():
    # no-op
    pass
