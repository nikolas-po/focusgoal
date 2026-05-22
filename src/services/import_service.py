"""Сервис импорта данных (ТЗ FR-011)"""
import json
import csv
from pathlib import Path
from sqlalchemy.orm import Session
from src.config.settings import Settings
from datetime import datetime, date


class ImportService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.settings = Settings()

    def import_from_json(self, input_path: str, mode: str = "add") -> dict:
        """mode: add | replace | skip"""
        from src.models.goal import Goal
        from src.models.habit import Habit

        raw = Path(input_path).read_bytes()

        if raw[:5] == b"FGENC" and self.settings.ENCRYPTION_KEY:
            from src.services.encryption_service import EncryptionService
            salt = raw[5:21]
            encrypted = raw[21:]
            crypto = EncryptionService(self.settings.ENCRYPTION_KEY, salt)
            data = json.loads(crypto.decrypt(encrypted).decode("utf-8"))
        else:
            data = json.loads(raw.decode("utf-8"))

        result = {"imported_goals": 0, "imported_habits": 0,
                  "skipped": 0, "replaced": 0, "errors": []}

        for gd in data.get("goals", []):
            try:
                existing = self.db.query(Goal).filter(
                    Goal.user_id == self.user_id, Goal.name == gd["name"]
                ).first()
                if existing:
                    if mode == "skip":
                        result["skipped"] += 1
                    elif mode == "replace":
                        for f in ["description", "priority_id", "repeat_type_id",
                                  "fail_behavior_id", "status_id"]:
                            if f in gd:
                                setattr(existing, f, gd[f])
                        if gd.get("deadline"):
                            existing.deadline = datetime.fromisoformat(gd["deadline"])
                        result["replaced"] += 1
                    else:
                        result["skipped"] += 1
                    continue
                goal_description = gd.get("description")
                if isinstance(goal_description, str) and not goal_description.strip():
                    goal_description = None
                goal = Goal(user_id=self.user_id, name=gd["name"],
                            description=goal_description,
                            priority_id=gd.get("priority_id", 2),
                            repeat_type_id=gd.get("repeat_type_id", 1),
                            fail_behavior_id=gd.get("fail_behavior_id", 2),
                            status_id=gd.get("status_id", 1))
                if gd.get("deadline"):
                    goal.deadline = datetime.fromisoformat(gd["deadline"])
                self.db.add(goal)
                result["imported_goals"] += 1
            except Exception as e:
                result["errors"].append(f"Цель: {e}")

        for hd in data.get("habits", []):
            try:
                existing = self.db.query(Habit).filter(
                    Habit.user_id == self.user_id, Habit.name == hd["name"]
                ).first()
                if existing:
                    if mode == "skip":
                        result["skipped"] += 1
                    elif mode == "replace":
                        for f in ["type_id", "mode_id", "target_value", "status_id"]:
                            if f in hd:
                                setattr(existing, f, hd[f])
                        if "description" in hd:
                            existing.description = hd.get("description") or None
                        result["replaced"] += 1
                    else:
                        result["skipped"] += 1
                    continue
                habit_description = hd.get("description")
                if isinstance(habit_description, str) and not habit_description.strip():
                    habit_description = None
                habit = Habit(user_id=self.user_id, name=hd["name"],
                              description=habit_description,
                              type_id=hd.get("type_id", 1),
                              mode_id=hd.get("mode_id", 1),
                              target_value=hd.get("target_value"),
                              status_id=hd.get("status_id", 1),
                              start_date=date.today())
                self.db.add(habit)
                result["imported_habits"] += 1
            except Exception as e:
                result["errors"].append(f"Привычка: {e}")

        self.db.commit()
        return result

    def import_from_csv(self, input_path: str) -> dict:
        from src.models.goal import Goal
        from src.models.habit import Habit

        result = {"imported_goals": 0, "imported_habits": 0, "errors": []}
        section = None

        with open(input_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or not row[0].strip():
                    continue
                cell = row[0].strip()
                if "=== ЦЕЛИ ===" in cell:
                    section = "goals"
                    next(reader, None)
                    continue
                elif "=== ПРИВЫЧКИ ===" in cell:
                    section = "habits"
                    next(reader, None)
                    continue
                elif cell.startswith("#") or cell.startswith("==="):
                    section = None
                    continue
                if section == "goals" and len(row) >= 2:
                    try:
                        description = row[2][:500].strip() if len(row) > 2 else None
                        if not description:
                            description = None
                        self.db.add(Goal(user_id=self.user_id, name=row[1][:100],
                                         description=description,
                                         status_id=1))
                        result["imported_goals"] += 1
                    except Exception as e:
                        result["errors"].append(str(e))
                elif section == "habits" and len(row) >= 2:
                    try:
                        self.db.add(Habit(user_id=self.user_id, name=row[1][:100],
                                          type_id=1, mode_id=1, status_id=1,
                                          start_date=date.today()))
                        result["imported_habits"] += 1
                    except Exception as e:
                        result["errors"].append(str(e))

        self.db.commit()
        return result
