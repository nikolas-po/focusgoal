"""002 add gdpr_consent to user

Revision ID: 002
Revises: 001
Create Date: 2025-05-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column("gdpr_consent", sa.DateTime, nullable=True)
    )


def downgrade():
    op.drop_column("user", "gdpr_consent")
