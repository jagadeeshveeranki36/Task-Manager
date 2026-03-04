"""Desktop notification wrapper using plyer."""

import logging

logger = logging.getLogger(__name__)

try:
    from plyer import notification as _plyer_notification
    _PLYER_AVAILABLE = True
except ImportError:
    _PLYER_AVAILABLE = False
    logger.warning("plyer not available — desktop notifications disabled.")


def send_notification(title: str, message: str, timeout: int = 8) -> None:
    """Send a desktop toast notification.

    Falls back to a console log if plyer is unavailable.
    """
    if _PLYER_AVAILABLE:
        try:
            _plyer_notification.notify(
                title=title,
                message=message,
                app_name="Task Manager",
                timeout=timeout,
            )
            logger.debug("Sent desktop notification: %r", title)
        except Exception as exc:
            logger.warning("plyer notification failed: %s", exc)
    else:
        logger.info("[NOTIFICATION] %s — %s", title, message)
