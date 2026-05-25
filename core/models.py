"""Task data model for Task Manager."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    id: int
    title: str
    description: str = ""
    due_datetime: Optional[str] = None   # ISO 8601 e.g. "2026-03-04T15:30:00"
    priority: str = "Medium"             # "Low" | "Medium" | "High"
    completed: bool = False
    snoozed_until: Optional[str] = None  # ISO 8601
    last_notified_at: Optional[str] = None  # ISO 8601
    created_at: str = ""

    # ── Convenience helpers ───────────────────────────────────────────────────

    @property
    def due_dt(self) -> Optional[datetime]:
        """Parse due_datetime string into a datetime object."""
        if self.due_datetime:
            try:
                return datetime.fromisoformat(self.due_datetime)
            except ValueError:
                return None
        return None

    @property
    def snoozed_dt(self) -> Optional[datetime]:
        if self.snoozed_until:
            try:
                return datetime.fromisoformat(self.snoozed_until)
            except ValueError:
                return None
        return None

    @property
    def last_notified_dt(self) -> Optional[datetime]:
        if self.last_notified_at:
            try:
                return datetime.fromisoformat(self.last_notified_at)
            except ValueError:
                return None
        return None

    def is_overdue(self) -> bool:
        """True if task has a due time that has passed and is not completed."""
        if self.completed or not self.due_dt:
            return False
        return datetime.now() > self.due_dt

    def is_due_soon(self, minutes: int = 10) -> bool:
        """True if task is due within the next *minutes* minutes."""
        if self.completed or not self.due_dt:
            return False
        delta = (self.due_dt - datetime.now()).total_seconds()
        return 0 < delta <= minutes * 60

    def needs_reminder(self, cooldown_seconds: int = 300) -> bool:
        """True if this task should fire a reminder right now.

        Conditions:
        - Not completed
        - Has a due datetime that has passed (or is right now)
        - Not currently snoozed
        - Has not been notified within the last cooldown_seconds
        """
        if self.completed or not self.due_dt:
            return False
        now = datetime.now()
        if now < self.due_dt:
            return False
        # Respect snooze
        if self.snoozed_dt and now < self.snoozed_dt:
            return False
        # Prevent duplicate notifications within cooldown window
        if self.last_notified_dt:
            elapsed = (now - self.last_notified_dt).total_seconds()
            if elapsed < cooldown_seconds:
                return False
        return True

    @staticmethod
    def from_dict(d: dict) -> "Task":
        return Task(
            id=d["id"],
            title=d["title"],
            description=d.get("description", "") or "",
            due_datetime=d.get("due_datetime"),
            priority=d.get("priority", "Medium") or "Medium",
            completed=bool(d.get("completed", 0)),
            snoozed_until=d.get("snoozed_until"),
            last_notified_at=d.get("last_notified_at"),
            created_at=d.get("created_at", ""),
        )
