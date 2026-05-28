"""Тесты StatisticsService (ТЗ FR-005, FR-007)"""
import pytest
from src.services.statistics_service import StatisticsService


class TestStatisticsService:
    def test_dashboard_empty_user(self, db_session):
        svc = StatisticsService(db_session)
        st  = svc.get_dashboard_statistics(99999)
        assert st["goals"]["total"]          == 0
        assert st["goals"]["completed"]      == 0
        assert st["goals"]["rate"]           == 0.0
        assert st["habits"]["total"]         == 0
        assert st["focus"]["total_minutes"]  == 0

    def test_dashboard_with_data(self, db_session, test_user, test_goal, test_habit):
        svc = StatisticsService(db_session)
        st  = svc.get_dashboard_statistics(test_user["id"])
        assert st["goals"]["total"]  >= 1
        assert st["habits"]["total"] >= 1

    def test_goals_rate_calculation(self, db_session, test_user):
        from src.services.goal_service import GoalService
        gsvc = GoalService(db_session)
        g1 = gsvc.create_goal(test_user["id"], {"name":"Цель А","status_id":1,"priority_id":1})
        g2 = gsvc.create_goal(test_user["id"], {"name":"Цель Б","status_id":1,"priority_id":2})
        gsvc.complete_goal(g1.id, test_user["id"])

        svc = StatisticsService(db_session)
        st  = svc.get_dashboard_statistics(test_user["id"])
        assert st["goals"]["completed"] >= 1
        assert st["goals"]["rate"]      >  0

    def test_heatmap_empty(self, db_session, test_user):
        svc  = StatisticsService(db_session)
        data = svc.get_heatmap_data(test_user["id"])
        assert isinstance(data, dict)

    def test_heatmap_with_completions(self, db_session, test_user, test_habit):
        from src.services.habit_service import HabitService
        hsvc = HabitService(db_session)
        hsvc.mark_completed(test_habit.id, test_user["id"])
        hsvc.mark_completed(test_habit.id, test_user["id"])

        svc  = StatisticsService(db_session)
        data = svc.get_heatmap_data(test_user["id"])
        assert isinstance(data, dict)

    def test_goals_by_period(self, db_session, test_user, test_goal):
        svc  = StatisticsService(db_session)
        data = svc.get_goals_by_period(test_user["id"], 30)
        assert isinstance(data, list)

    def test_focus_status_distribution(self, db_session, test_user):
        svc  = StatisticsService(db_session)
        dist = svc.get_focus_status_distribution(test_user["id"])
        assert "completed"   in dist
        assert "cancelled"   in dist
        assert "interrupted" in dist
        assert all(isinstance(v, int) for v in dist.values())
