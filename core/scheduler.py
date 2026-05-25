"""Background scheduler for task reminders."""

import logging
from datetime import datetime
from typing import Callable, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SCHEDULER_INTERVAL, NOTIFICATION_COOLDOWN
from core.database import get_all_tasks, set_last_notified
from core.models import Task
from core.notifications import send_notification

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Fires reminders in two ways:
      1. Exact date job — fires at the precise due_datetime second.
      2. Poll job (every SCHEDULER_INTERVAL seconds) — catches overdue tasks
         that were added after the exact job window or missed for any reason.
    """

    def __init__(self, reminder_callback: Optional[Callable[[Task], None]] = None):
        self._scheduler = BackgroundScheduler(daemon=True)
        self._reminder_callback = reminder_callback
        self._is_running = False
        # track which task ids have exact jobs scheduled
        self._exact_job_ids: set[int] = set()

    def set_reminder_callback(self, cb: Callable[[Task], None]) -> None:
        self._reminder_callback = cb

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._is_running:
            return
        self._scheduler.add_job(
            self._poll,
            trigger="interval",
            seconds=SCHEDULER_INTERVAL,
            id="task_poll",
            replace_existing=True,
            max_instances=1,
        )
        self._scheduler.start()
        self._is_running = True
        logger.info("Scheduler started (interval=%ds)", SCHEDULER_INTERVAL)

    def shutdown(self, wait: bool = False) -> None:
        if self._is_running:
            try:
                self._scheduler.shutdown(wait=wait)
                logger.info("Scheduler shut down.")
            except Exception as exc:
                logger.warning("Scheduler shutdown error: %s", exc)
            self._is_running = False

    # ── Exact-time job management ─────────────────────────────────────────────

    def schedule_exact(self, task: Task) -> None:
        """Schedule a one-shot job that fires exactly at task.due_datetime."""
        if not task.due_datetime or task.completed:
            return
        due_dt = task.due_dt
        if due_dt is None or due_dt <= datetime.now():
            return  # already past — poll will catch it

        job_id = f"exact_{task.id}"
        try:
            self._scheduler.add_job(
                self._fire_exact,
                trigger=DateTrigger(run_date=due_dt),
                id=job_id,
                replace_existing=True,
                args=[task],
            )
            self._exact_job_ids.add(task.id)
            logger.info("Exact job scheduled for task %s at %s", task.id, due_dt)
        except Exception as exc:
            logger.warning("Could not schedule exact job for task %s: %s", task.id, exc)

    def cancel_exact(self, task_id: int) -> None:
        """Remove the exact job for a task (e.g. when it's deleted or completed)."""
        job_id = f"exact_{task_id}"
        try:
            self._scheduler.remove_job(job_id)
            self._exact_job_ids.discard(task_id)
        except Exception:
            pass  # job may not exist — that's fine

    def schedule_all_exact(self, tasks) -> None:
        """Bulk-schedule exact jobs for all upcoming tasks."""
        for task in tasks:
            self.schedule_exact(task)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _fire_exact(self, task: Task) -> None:
        """One-shot callback at the precise due second."""
        self._exact_job_ids.discard(task.id)
        logger.info("Exact reminder fired for task id=%s %r", task.id, task.title)
        set_last_notified(task.id)
        send_notification(
            title="⏰ Task Due Now",
            message=f"{task.title} is due right now!",
        )
        if self._reminder_callback:
            try:
                self._reminder_callback(task)
            except Exception as exc:
                logger.exception("Reminder callback error: %s", exc)

    def _poll(self) -> None:
        """Fallback poll — catches overdue tasks missed by the exact job."""
        try:
            rows = get_all_tasks()
            tasks = [Task.from_dict(r) for r in rows]
            for task in tasks:
                # Skip tasks that have an exact job pending (they haven't fired yet)
                if task.id in self._exact_job_ids:
                    continue
                if task.needs_reminder(cooldown_seconds=NOTIFICATION_COOLDOWN):
                    logger.info("Poll reminder for task id=%s %r", task.id, task.title)
                    set_last_notified(task.id)
                    send_notification(
                        title="⏰ Task Reminder",
                        message=f"Don't forget: {task.title}",
                    )
                    if self._reminder_callback:
                        try:
                            self._reminder_callback(task)
                        except Exception as cb_exc:
                            logger.exception("Reminder callback error: %s", cb_exc)
        except Exception as exc:
            logger.exception("Scheduler poll error: %s", exc)


# Singleton instance
scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    global scheduler
    if scheduler is None:
        scheduler = TaskScheduler()
    return scheduler
