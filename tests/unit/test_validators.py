"""Тесты валидаторов"""
import pytest
from src.utils.validators import (
    validate_email, validate_password,
    validate_nickname, validate_goal_name, validate_habit_name
)


class TestValidateEmail:
    def test_valid(self):
        assert validate_email("user@example.com") is True
        assert validate_email("user.name+tag@sub.domain.ru") is True

    def test_invalid_no_at(self):
        assert validate_email("notanemail") is False

    def test_invalid_no_domain(self):
        assert validate_email("user@") is False

    def test_invalid_empty(self):
        assert validate_email("") is False

    def test_invalid_none(self):
        assert validate_email(None) is False


class TestValidatePassword:
    def test_valid(self):
        assert validate_password("Password123") is True
        assert validate_password("abc12345") is True

    def test_too_short(self):
        assert validate_password("Abc1") is False

    def test_no_letters(self):
        assert validate_password("12345678") is False

    def test_no_digits(self):
        assert validate_password("abcdefgh") is False

    def test_empty(self):
        assert validate_password("") is False


class TestValidateNickname:
    def test_valid(self):
        assert validate_nickname("user123") is True
        assert validate_nickname("abc") is True

    def test_too_short(self):
        assert validate_nickname("ab") is False

    def test_too_long(self):
        assert validate_nickname("a" * 51) is False

    def test_empty(self):
        assert validate_nickname("") is False


class TestValidateGoalName:
    def test_valid(self):
        assert validate_goal_name("Моя цель") is True
        assert validate_goal_name("abc") is True

    def test_too_short(self):
        assert validate_goal_name("ab") is False

    def test_empty(self):
        assert validate_goal_name("") is False
        assert validate_goal_name(None) is False
