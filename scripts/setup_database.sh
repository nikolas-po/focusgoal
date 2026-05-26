#!/bin/bash
# Первоначальная настройка PostgreSQL для FocusGoal
set -e

DB_NAME="${DB_NAME:-focusgoal_db}"
DB_USER="${DB_USER:-focusgoal}"
DB_PASSWORD="${DB_PASSWORD:-password}"
DB_HOST="${DB_HOST:-localhost}"

echo " Настройка базы данных FocusGoal "
echo "База: $DB_NAME | Пользователь: $DB_USER | Хост: $DB_HOST"

sudo -u postgres psql << EOSQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
    CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    RAISE NOTICE 'Пользователь $DB_USER создан';
  ELSE
    ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    RAISE NOTICE 'Пароль пользователя $DB_USER обновлён';
  END IF;
END
\$\$;

SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS $DB_NAME;

CREATE DATABASE $DB_NAME
  OWNER $DB_USER
  ENCODING 'UTF8'
  LC_COLLATE = 'ru_RU.UTF-8'
  LC_CTYPE   = 'ru_RU.UTF-8'
  TEMPLATE   = template0;

GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOSQL

echo ""
echo "База данных '$DB_NAME' создана."
echo ""
echo "Следующие шаги:"
echo "  1. cp .env.example .env"
echo "  2. Отредактируйте .env (DB_PASSWORD, ENCRYPTION_KEY)"
echo "  3. python -m alembic upgrade head"
echo "  4. python run.py"
