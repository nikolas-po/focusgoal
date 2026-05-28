"""Тесты поиска по всем полям (ТЗ FR-002, FR-003).

Проверяет фильтрацию целей и привычек по тексту:
название, описание, статус (текст), приоритет (текст), дедлайн (строка).
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Вспомогательные функции — дублируют логику goal_window.py и habit_window.py
# без зависимости от PyQt (чисто Python)
# ---------------------------------------------------------------------------

PRIORITY_NAMES = {1: "Высокий", 2: "Средний", 3: "Низкий"}
GOAL_STATUS_NAMES = {1: "Активная", 2: "Выполнена", 3: "Просрочена",
                     4: "Удалена", 5: "В архиве"}
HABIT_TYPE_NAMES = {1: "ежедневная", 2: "еженедельная", 3: "ежемесячная"}
HABIT_MODE_NAMES = {1: "бинарная", 2: "количественная"}
HABIT_STATUS_NAMES = {1: "активная", 2: "в архиве", 3: "отключённая", 4: "удалена"}


def _goal_matches(goal, search_text: str) -> bool:
    """Логика поиска из goal_window.py (GoalWindow.load_goals)."""
    q = search_text.strip().lower()
    if not q:
        return True
    deadline_str = goal.deadline.strftime("%d.%m.%Y") if goal.deadline else ""
    fields = [
        (goal.name or "").lower(),
        (goal.description or "").lower(),
        PRIORITY_NAMES.get(goal.priority_id, "").lower(),
        GOAL_STATUS_NAMES.get(goal.status_id, "").lower(),
        deadline_str.lower(),
    ]
    return any(q in f for f in fields)


def _habit_matches(habit, search_text: str) -> bool:
    """Логика поиска из habit_window.py (HabitWindow._load_habits)."""
    q = search_text.strip().lower()
    if not q:
        return True
    fields = [
        (habit.name or "").lower(),
        (habit.description or "").lower(),
        HABIT_TYPE_NAMES.get(habit.type_id, "").lower(),
        HABIT_MODE_NAMES.get(habit.mode_id, "").lower(),
        HABIT_STATUS_NAMES.get(habit.status_id, "").lower(),
        str(habit.current_streak),
    ]
    return any(q in f for f in fields)


def _make_goal(name="Цель", description="", priority_id=1,
               status_id=1, deadline=None):
    g = MagicMock()
    g.name = name
    g.description = description
    g.priority_id = priority_id
    g.status_id = status_id
    g.deadline = deadline
    return g


def _make_habit(name="Привычка", description="", type_id=1,
                mode_id=1, status_id=1, current_streak=0):
    h = MagicMock()
    h.name = name
    h.description = description
    h.type_id = type_id
    h.mode_id = mode_id
    h.status_id = status_id
    h.current_streak = current_streak
    return h


# ---------------------------------------------------------------------------
# Тесты поиска по целям (ТЗ FR-002.5)
# ---------------------------------------------------------------------------

class TestGoalSearch:

    def test_empty_query_returns_all(self):
        goals = [_make_goal("Цель 1"), _make_goal("Цель 2")]
        result = [g for g in goals if _goal_matches(g, "")]
        assert len(result) == 2

    def test_search_by_name(self):
        goals = [_make_goal("Выучить Python"), _make_goal("Купить книгу")]
        result = [g for g in goals if _goal_matches(g, "python")]
        assert len(result) == 1
        assert result[0].name == "Выучить Python"

    def test_search_by_description(self):
        goals = [
            _make_goal("Цель 1", description="Важный проект по алгоритмам"),
            _make_goal("Цель 2", description="Личные дела"),
        ]
        result = [g for g in goals if _goal_matches(g, "алгоритм")]
        assert len(result) == 1

    def test_search_by_priority_high(self):
        goals = [
            _make_goal("A", priority_id=1),  # Высокий
            _make_goal("B", priority_id=3),  # Низкий
        ]
        result = [g for g in goals if _goal_matches(g, "высокий")]
        assert len(result) == 1
        assert result[0].name == "A"

    def test_search_by_status_completed(self):
        goals = [
            _make_goal("A", status_id=1),  # Активная
            _make_goal("B", status_id=2),  # Выполнена
        ]
        result = [g for g in goals if _goal_matches(g, "выполн")]
        assert len(result) == 1
        assert result[0].name == "B"

    def test_search_by_deadline_date(self):
        target_date = datetime(2025, 12, 31)
        goals = [
            _make_goal("C цедлайном", deadline=target_date),
            _make_goal("Без дедлайна", deadline=None),
        ]
        result = [g for g in goals if _goal_matches(g, "31.12.2025")]
        assert len(result) == 1

    def test_search_case_insensitive(self):
        goals = [_make_goal("Изучить DJANGO"), _make_goal("Другое")]
        result = [g for g in goals if _goal_matches(g, "django")]
        assert len(result) == 1

    def test_search_partial_match(self):
        goals = [_make_goal("Изучить Python"), _make_goal("Другое")]
        result = [g for g in goals if _goal_matches(g, "учить")]
        assert len(result) == 1

    def test_search_no_match(self):
        goals = [_make_goal("Цель 1"), _make_goal("Цель 2")]
        result = [g for g in goals if _goal_matches(g, "xyz_not_existing")]
        assert len(result) == 0

    def test_search_with_spaces(self):
        """Пробелы в запросе не должны вызывать ошибок."""
        goals = [_make_goal("Тестовая цель")]
        result = [g for g in goals if _goal_matches(g, "  тестовая  ")]
        assert len(result) == 1

    def test_search_overdue_status(self):
        goals = [
            _make_goal("Старая цель", status_id=3),  # Просрочена
            _make_goal("Новая цель", status_id=1),
        ]
        result = [g for g in goals if _goal_matches(g, "просроч")]
        assert len(result) == 1

    def test_search_goal_no_deadline(self):
        """Цели без дедлайна не должны падать при поиске."""
        goals = [_make_goal("Без дедлайна", deadline=None)]
        result = [g for g in goals if _goal_matches(g, "декабрь")]
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Тесты поиска по привычкам (ТЗ FR-003.5)
# ---------------------------------------------------------------------------

class TestHabitSearch:

    def test_empty_query_returns_all(self):
        habits = [_make_habit("A"), _make_habit("B")]
        result = [h for h in habits if _habit_matches(h, "")]
        assert len(result) == 2

    def test_search_by_name(self):
        habits = [
            _make_habit("Зарядка каждый день"),
            _make_habit("Читать книги"),
        ]
        result = [h for h in habits if _habit_matches(h, "зарядка")]
        assert len(result) == 1

    def test_search_by_description(self):
        habits = [
            _make_habit("Привычка 1", description="Бегать по утрам"),
            _make_habit("Привычка 2", description="Вечерние прогулки"),
        ]
        # "утрам" содержит "утр" — используем общий корень
        result = [h for h in habits if _habit_matches(h, "утр")]
        assert len(result) == 1

    def test_search_by_type_daily(self):
        habits = [
            _make_habit("Ежедневная задача", type_id=1),
            _make_habit("Раз в неделю", type_id=2),
        ]
        result = [h for h in habits if _habit_matches(h, "ежедневная")]
        assert len(result) == 1

    def test_search_by_type_weekly(self):
        habits = [
            _make_habit("A", type_id=1),
            _make_habit("B", type_id=2),
            _make_habit("C", type_id=3),
        ]
        result = [h for h in habits if _habit_matches(h, "еженедельная")]
        assert len(result) == 1
        assert result[0].name == "B"

    def test_search_by_mode_binary(self):
        habits = [
            _make_habit("Бинарная привычка", mode_id=1),
            _make_habit("Количественная", mode_id=2),
        ]
        result = [h for h in habits if _habit_matches(h, "бинар")]
        assert len(result) == 1

    def test_search_by_mode_quantitative(self):
        habits = [
            _make_habit("A", mode_id=1),
            _make_habit("B", mode_id=2),
        ]
        result = [h for h in habits if _habit_matches(h, "количест")]
        assert len(result) == 1
        assert result[0].name == "B"

    def test_search_by_status_active(self):
        habits = [
            _make_habit("A", status_id=1),  # активная
            _make_habit("B", status_id=2),  # в архиве
        ]
        result = [h for h in habits if _habit_matches(h, "активная")]
        assert len(result) == 1
        assert result[0].name == "A"

    def test_search_by_status_archived(self):
        habits = [
            _make_habit("A", status_id=1),
            _make_habit("Архивная", status_id=2),
        ]
        result = [h for h in habits if _habit_matches(h, "архив")]
        assert len(result) == 1

    def test_search_by_streak_number(self):
        habits = [
            _make_habit("A", current_streak=7),
            _make_habit("B", current_streak=14),
        ]
        result = [h for h in habits if _habit_matches(h, "14")]
        assert len(result) == 1
        assert result[0].name == "B"

    def test_search_case_insensitive(self):
        habits = [_make_habit("МЕДИТАЦИЯ"), _make_habit("Другое")]
        result = [h for h in habits if _habit_matches(h, "медита")]
        assert len(result) == 1

    def test_search_no_match_returns_empty(self):
        habits = [_make_habit("A"), _make_habit("B")]
        result = [h for h in habits if _habit_matches(h, "zzznomatch")]
        assert len(result) == 0

    def test_search_disabled_habit(self):
        habits = [
            _make_habit("A", status_id=3),   # отключённая
            _make_habit("B", status_id=1),
        ]
        result = [h for h in habits if _habit_matches(h, "отключ")]
        assert len(result) == 1
        assert result[0].name == "A"
