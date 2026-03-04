"""Background scheduler for task reminders."""

import logging
from typing import Callable, Optional

from apscheduler.schedulers.background import BackgroundScheduler

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SCHEDULER_INTERVAL
from core.database import get_all_tasks, set_last_notified
from core.models import Task
from core.notifications import send_notification

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Polls for overdue tasks and fires reminder callbacks."""

    def __init__(self, reminder_callback: Optional[Callable[[Task], None]] = None):
        """
        Args:
            reminder_callback: Called on the scheduler thread when a task needs
                               a reminder. The UI layer should use `after()` to
                               marshal this onto the Tk main thread.
        """
        self._scheduler = BackgroundScheduler(daemon=True)
        self._reminder_callback = reminder_callback
        self._is_running = False

    def set_reminder_callback(self, cb: Callable[[Task], None]) -> None:
        self._reminder_callback = cb

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

    def _poll(self) -> None:
        """Check all tasks and fire reminders as needed."""
        try:
            rows = get_all_tasks()
            tasks = [Task.from_dict(r) for r in rows]
            for task in tasks:
                if task.needs_reminder(interval_seconds=SCHEDULER_INTERVAL):
                    logger.info("Reminder triggered for task id=%s %r", task.id, task.title)
                    # Mark notified immediately to prevent duplicate callbacks
                    set_last_notified(task.id)
                    # Send a system toast as well
                    send_notification(
                        title="⏰ Task Reminder",
                        message=f"Don't forget: {task.title}",
                    )
                    # Invoke the UI callback on the scheduler thread;
                    # the UI layer is responsible for marshalling to the main thread.
                    if self._reminder_callback:
                        try:
                            self._reminder_callback(task)
                        except Exception as cb_exc:
                            logger.exception("Reminder callback error: %s", cb_exc)
        except Exception as exc:
            logger.exception("Scheduler poll error: %s", exc)


# Singleton instance (created in main.py after logging is set up)
scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    global scheduler
    if scheduler is None:
        scheduler = TaskScheduler()
    return scheduler
