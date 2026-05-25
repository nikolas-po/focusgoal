#!/bin/bash
# Запуск тестов с отчётом покрытия
set -e
echo "Тесты FocusGoal "
python -m pytest tests/ -v \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html:coverage_report \
  --tb=short
echo ""
echo "Отчёт о покрытии: coverage_report/index.html"
