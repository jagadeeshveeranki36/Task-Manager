"""Reminder popup dialog for overdue tasks."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

import customtkinter as ctk

from config import THEME_COLORS, SNOOZE_MINUTES
from core.models import Task
from core import database as db

logger = logging.getLogger(__name__)

C = THEME_COLORS


class ReminderPopup(ctk.CTkToplevel):
    """Alert-style reminder popup — fires when a task becomes due."""

    # Alert palette (orange/amber — distinct from the app's green theme)
    _ALERT_BG      = "#FFF8F0"
    _ALERT_BANNER  = "#E67E22"   # amber
    _ALERT_BANNER2 = "#D35400"   # darker amber for gradient effect
    _ALERT_TEXT    = "#7D3C00"
    _ALERT_PILL    = "#FDEBD0"
    _ALERT_BORDER  = "#F0A500"

    def __init__(
        self,
        parent,
        task: Task,
        on_complete: Optional[Callable[[Task], None]] = None,
    ):
        super().__init__(parent)
        self._task = task
        self._on_complete = on_complete

        self.title("⚠️ Task Alert")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()
        self.focus_force()

        self._build_ui()
        self._center(parent)

        # Pulse the window border for 1 second to grab attention
        self._pulse(3)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.configure(fg_color=self._ALERT_BG)

        # ── Thick amber banner at top ──────────────────────────────────────────
        banner = ctk.CTkFrame(
            self,
            fg_color=self._ALERT_BANNER,
            corner_radius=0,
            height=56,
        )
        banner.pack(fill="x")
        banner.pack_propagate(False)

        banner_inner = ctk.CTkFrame(banner, fg_color="transparent")
        banner_inner.pack(expand=True)

        ctk.CTkLabel(
            banner_inner,
            text="⚠️  TASK ALERT",
            font=ctk.CTkFont("Segoe UI", 17, "bold"),
            text_color="#FFFFFF",
        ).pack(side="left", padx=(12, 0), pady=10)

        # ── Body ──────────────────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=(22, 8))

        # Warning icon
        ctk.CTkLabel(
            body,
            text="🔔",
            font=ctk.CTkFont(size=48),
        ).pack()

        # Primary message
        ctk.CTkLabel(
            body,
            text="You have to do this task:",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=self._ALERT_TEXT,
        ).pack(pady=(10, 4))

        # Task name pill — highly visible
        task_pill = ctk.CTkFrame(
            body,
            fg_color=self._ALERT_PILL,
            corner_radius=12,
            border_color=self._ALERT_BORDER,
            border_width=2,
        )
        task_pill.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            task_pill,
            text=self._task.title,
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            text_color=self._ALERT_BANNER2,
            wraplength=300,
            justify="center",
        ).pack(padx=16, pady=12)

        # Sub-message
        ctk.CTkLabel(
            body,
            text="Don't let this slip! Complete it now 💪",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color="#A04000",
            justify="center",
        ).pack(pady=(0, 6))

        # Due time (if set)
        if self._task.due_dt:
            due_str = self._task.due_dt.strftime("%d %b %Y at %H:%M")
            ctk.CTkLabel(
                body,
                text=f"🕐  Due: {due_str}",
                font=ctk.CTkFont("Segoe UI", 11),
                text_color="#C0611A",
            ).pack(pady=(0, 4))

        # Priority badge
        prio_color = {
            "High":   C["priority_high"],
            "Medium": C["priority_medium"],
            "Low":    C["priority_low"],
        }.get(self._task.priority, C["priority_low"])

        ctk.CTkLabel(
            body,
            text=f"  {self._task.priority} Priority  ",
            fg_color=prio_color,
            text_color="#FFFFFF",
            corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
        ).pack(pady=(4, 18))

        # ── Action buttons ────────────────────────────────────────────────────
        ctk.CTkButton(
            body,
            text="✅  Mark as Complete",
            height=44,
            corner_radius=12,
            fg_color=C["primary"],
            hover_color=C["primary_dark"],
            text_color="white",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            command=self._action_complete,
        ).pack(fill="x", pady=(0, 8))

        ctk.CTkButton(
            body,
            text=f"💤  Snooze {SNOOZE_MINUTES} min",
            height=38,
            corner_radius=12,
            fg_color="#FDEBD0",
            hover_color="#FAD7A0",
            text_color=self._ALERT_TEXT,
            font=ctk.CTkFont("Segoe UI", 13),
            command=self._action_snooze,
        ).pack(fill="x", pady=(0, 8))

        ctk.CTkButton(
            body,
            text="Dismiss",
            height=34,
            corner_radius=12,
            fg_color="transparent",
            hover_color="#FDEBD0",
            text_color="#A04000",
            border_width=1,
            border_color=self._ALERT_BORDER,
            font=ctk.CTkFont("Segoe UI", 13),
            command=self._action_dismiss,
        ).pack(fill="x", pady=(0, 16))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _action_complete(self):
        db.mark_complete(self._task.id, True)
        self._task.completed = True
        logger.info("Task %s marked complete from reminder popup", self._task.id)
        if self._on_complete:
            self._on_complete(self._task)
        self.destroy()

    def _action_snooze(self):
        snooze_dt = (datetime.now() + timedelta(minutes=SNOOZE_MINUTES)).isoformat(timespec="seconds")
        db.set_snoozed_until(self._task.id, snooze_dt)
        logger.info("Task %s snoozed until %s", self._task.id, snooze_dt)
        self.destroy()

    def _action_dismiss(self):
        db.set_last_notified(self._task.id)
        logger.info("Task %s reminder dismissed", self._task.id)
        self.destroy()

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _center(self, parent):
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")

    def _pulse(self, times: int, _on: bool = True):
        """Flash the banner colour to grab attention."""
        if times <= 0:
            return
        colour = self._ALERT_BANNER if _on else "#FFFFFF"
        try:
            self.configure(fg_color=colour)
        except Exception:
            return
        self.after(150, lambda: self._pulse(times - 1, not _on))

