#!/bin/bash
# Применение миграций Alembic
set -e
echo " Применение миграций FocusGoal "
python -m alembic upgrade head
echo "Миграции применены успешно."
