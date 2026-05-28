"""001 initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Справочники
    for table, extra_cols in [
        ("goal_status", []),
        ("goal_priority", []),
        ("goal_repeat_type", []),
        ("goal_fail_behavior", []),
        ("habit_type", []),
        ("habit_mode", []),
        ("habit_status", []),
        ("block_level", []),
        ("focus_session_status", []),
        ("notification_type", []),
        ("notification_delivery_status", []),
        ("completion_object_type", []),
        ("system_log_event_type", []),
    ]:
        op.create_table(
            table,
            sa.Column("id", sa.SmallInteger, primary_key=True),
            sa.Column("code", sa.String(30), nullable=False, unique=True),
            sa.Column("name_ru", sa.String(100), nullable=False),
            sa.Column("sort_order", sa.SmallInteger, default=0),
            sa.Column("is_active", sa.Boolean, default=True),
        )

    # Пользователи
    op.create_table(
        "user",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("nickname", sa.String(50), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("registered_at", sa.DateTime, nullable=False),
        sa.Column("timezone", sa.String(50), default="UTC"),
        sa.Column("settings", JSONB, default=dict),
        sa.Column("local_data_path", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.CheckConstraint("length(trim(nickname)) >= 3", name="chk_user_nickname_length"),
    )

    # Цели
    op.create_table(
        "goal",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("deadline", sa.DateTime, nullable=True),
        sa.Column("priority_id", sa.Integer, sa.ForeignKey("goal_priority.id"), default=2),
        sa.Column("repeat_type_id", sa.Integer, sa.ForeignKey("goal_repeat_type.id"), default=1),
        sa.Column("fail_behavior_id", sa.Integer, sa.ForeignKey("goal_fail_behavior.id"), default=2),
        sa.Column("status_id", sa.Integer, sa.ForeignKey("goal_status.id"), default=1),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.CheckConstraint("length(trim(name)) >= 3", name="chk_goal_name_length"),
    )
    op.create_index("ix_goal_user_id", "goal", ["user_id"])
    op.create_index("ix_goal_status_id", "goal", ["status_id"])

    # Привычки
    op.create_table(
        "habit",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("type_id", sa.Integer, sa.ForeignKey("habit_type.id"), default=1),
        sa.Column("mode_id", sa.Integer, sa.ForeignKey("habit_mode.id"), default=1),
        sa.Column("status_id", sa.Integer, sa.ForeignKey("habit_status.id"), default=1),
        sa.Column("target_value", sa.Integer, nullable=True),
        sa.Column("current_streak", sa.Integer, default=0),
        sa.Column("max_streak", sa.Integer, default=0),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("last_completed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.CheckConstraint("length(trim(name)) >= 3", name="chk_habit_name_length"),
    )
    op.create_index("ix_habit_user_id", "habit", ["user_id"])

    # Фокус-сессии
    op.create_table(
        "focus_session",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goal_id", sa.Integer, sa.ForeignKey("goal.id", ondelete="SET NULL"), nullable=True),
        sa.Column("start_time", sa.DateTime, nullable=False),
        sa.Column("planned_duration", sa.Integer, nullable=False),
        sa.Column("actual_duration", sa.Integer, nullable=True),
        sa.Column("status_id", sa.Integer, sa.ForeignKey("focus_session_status.id"), default=1),
        sa.Column("blocked_apps_count", sa.Integer, default=0),
        sa.Column("blocked_processes_list", JSONB, default=list),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.CheckConstraint("planned_duration > 0", name="chk_session_duration"),
    )
    op.create_index("ix_focus_session_user_id", "focus_session", ["user_id"])

    # Заблокированные приложения
    op.create_table(
        "blocked_app",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("app_name", sa.String(100), nullable=False),
        sa.Column("process_name", sa.String(255), nullable=False),
        sa.Column("block_level_id", sa.Integer, sa.ForeignKey("block_level.id"), default=1),
        sa.Column("block_time_limit", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # Журнал выполнений
    op.create_table(
        "completion_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("object_type_id", sa.Integer, sa.ForeignKey("completion_object_type.id"), nullable=False),
        sa.Column("object_id", sa.Integer, nullable=False),
        sa.Column("completed_at", sa.DateTime, nullable=False),
        sa.Column("progress", sa.Integer, nullable=True),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_completion_log_user_id", "completion_log", ["user_id"])

    # Уведомления
    op.create_table(
        "notification_schedule",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type_id", sa.Integer, sa.ForeignKey("notification_type.id"), default=1),
        sa.Column("send_at", sa.DateTime, nullable=False),
        sa.Column("delivery_status_id", sa.Integer,
                  sa.ForeignKey("notification_delivery_status.id"), default=2),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # Системный лог
    op.create_table(
        "system_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("event_at", sa.DateTime, nullable=False),
        sa.Column("event_type_id", sa.Integer, sa.ForeignKey("system_log_event_type.id"), default=3),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("context", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )


def downgrade():
    tables = [
        "system_log", "notification_schedule", "completion_log",
        "blocked_app", "focus_session", "habit", "goal", "user",
        "goal_status", "goal_priority", "goal_repeat_type",
        "goal_fail_behavior", "habit_type", "habit_mode", "habit_status",
        "block_level", "focus_session_status", "notification_type",
        "notification_delivery_status", "completion_object_type",
        "system_log_event_type",
    ]
    for t in tables:
        op.drop_table(t)
