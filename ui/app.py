"""Main application window for Task Manager."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import tkinter as tk
from typing import List, Optional

import customtkinter as ctk

from config import THEME_COLORS, APP_TITLE, WINDOW_SIZE, MIN_WINDOW_SIZE
from core import database as db
from core.models import Task
from core.scheduler import get_scheduler

from ui.task_card import TaskCard
from ui.add_edit_dialog import TaskDialog
from ui.reminder_popup import ReminderPopup

logger = logging.getLogger(__name__)

C = THEME_COLORS

SORT_OPTIONS = ["Due Date", "Priority", "Created", "Status"]
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


class SuccessToast(ctk.CTkToplevel):
    """Auto-closing success popup."""

    def __init__(self, parent, message: str = "You have successfully completed your task!"):
        super().__init__(parent)
        self.title("")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.configure(fg_color=C["success"])

        ctk.CTkLabel(
            self,
            text=f"  ✅  {message}  ",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color="white",
            fg_color=C["success"],
            corner_radius=12,
        ).pack(padx=20, pady=14)

        # Centre bottom of parent
        self.update_idletasks()
        pw = parent.winfo_width()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        ph = parent.winfo_height()
        w = self.winfo_reqwidth()
        x = px + (pw - w) // 2
        y = py + ph - self.winfo_reqheight() - 60
        self.geometry(f"+{x}+{y}")

        # Auto-close after 2 seconds
        self.after(2000, self.destroy)


class App(ctk.CTk):
    """Main Task Manager window."""

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(*MIN_WINDOW_SIZE)
        self.configure(fg_color=C["bg"])

        # Pending reminder tasks (queued from scheduler thread)
        self._pending_reminders: List[Task] = []
        # Track task IDs that currently have an open popup (prevent duplicates)
        self._active_popups: set = set()

        self._build_ui()
        self._setup_scheduler()
        self.load_tasks()

        # Poll for pending reminders every 100 ms on the main thread
        self.after(100, self._check_pending_reminders)

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(
            self,
            fg_color=C["toolbar"],
            corner_radius=0,
            border_width=1,
            border_color=C["toolbar_border"],
        )
        toolbar.pack(fill="x", side="top")

        toolbar_inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        toolbar_inner.pack(fill="x", padx=24, pady=12)

        # App logo / title
        logo_frame = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        logo_frame.pack(side="left")

        ctk.CTkLabel(
            logo_frame,
            text="✅",
            font=ctk.CTkFont(size=26),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            logo_frame,
            text=APP_TITLE,
            font=ctk.CTkFont("Segoe UI", 20, "bold"),
            text_color=C["text"],
        ).pack(side="left")

        # Right-side controls
        right = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        right.pack(side="right")

        # Sort dropdown
        ctk.CTkLabel(
            right,
            text="Sort by:",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=C["text_secondary"],
        ).pack(side="left", padx=(0, 6))

        self._sort_var = ctk.StringVar(value="Due Date")
        sort_menu = ctk.CTkOptionMenu(
            right,
            values=SORT_OPTIONS,
            variable=self._sort_var,
            width=130,
            height=36,
            corner_radius=10,
            fg_color=C["surface"],
            button_color=C["primary"],
            button_hover_color=C["primary_dark"],
            text_color=C["text"],
            font=ctk.CTkFont("Segoe UI", 12),
            command=lambda _: self.load_tasks(),
        )
        sort_menu.pack(side="left", padx=(0, 16))

        # Add Task button
        ctk.CTkButton(
            right,
            text="＋  Add Task",
            width=130,
            height=38,
            corner_radius=12,
            fg_color=C["primary"],
            hover_color=C["primary_dark"],
            text_color=C["btn_primary_fg"],
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            command=self.show_add_dialog,
        ).pack(side="left")

        # ── Main content area ─────────────────────────────────────────────────
        content = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        content.pack(fill="both", expand=True, padx=0, pady=0)

        # Stats bar
        self._stats_frame = ctk.CTkFrame(content, fg_color="transparent")
        self._stats_frame.pack(fill="x", padx=28, pady=(16, 0))

        # Scrollable task list
        self._scroll_frame = ctk.CTkScrollableFrame(
            content,
            fg_color="transparent",
            scrollbar_button_color=C["primary_light"],
            scrollbar_button_hover_color=C["primary"],
            corner_radius=0,
        )
        self._scroll_frame.pack(fill="both", expand=True, padx=20, pady=12)

        # Empty state
        self._empty_frame = ctk.CTkFrame(content, fg_color="transparent")
        ctk.CTkLabel(
            self._empty_frame,
            text="🗒️",
            font=ctk.CTkFont(size=48),
        ).pack(pady=(60, 8))
        ctk.CTkLabel(
            self._empty_frame,
            text="No tasks yet",
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            text_color=C["text"],
        ).pack()
        ctk.CTkLabel(
            self._empty_frame,
            text="Click  ＋ Add Task  to get started",
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=C["text_muted"],
        ).pack(pady=(4, 0))

    # ── Scheduler setup ───────────────────────────────────────────────────────

    def _setup_scheduler(self):
        sched = get_scheduler()
        sched.set_reminder_callback(self._on_reminder_received)
        sched.start()

    def _schedule_exact_for_tasks(self, tasks):
        """Register exact-time jobs with the scheduler for all upcoming tasks."""
        sched = get_scheduler()
        sched.schedule_all_exact(tasks)

    def _on_reminder_received(self, task: Task):
        """Called from scheduler thread — queue for main thread processing."""
        # Deduplicate: ignore if this task is already queued or showing
        if task.id not in self._active_popups and not any(
            t.id == task.id for t in self._pending_reminders
        ):
            self._pending_reminders.append(task)

    def _check_pending_reminders(self):
        """Drain the pending reminders queue on the main Tk thread."""
        while self._pending_reminders:
            task = self._pending_reminders.pop(0)
            self._show_reminder_popup(task)
        self.after(100, self._check_pending_reminders)

    def _show_reminder_popup(self, task: Task):
        # Guard: don't open a second popup for the same task
        if task.id in self._active_popups:
            return
        try:
            self._active_popups.add(task.id)

            def _on_close(t: Task):
                self._active_popups.discard(t.id)
                self._handle_complete(t)

            def _on_popup_done(task_id: int):
                self._active_popups.discard(task_id)

            popup = ReminderPopup(
                self, task,
                on_complete=_on_close,
                on_dismiss=lambda: _on_popup_done(task.id),
            )
            # Lift above main window and focus
            popup.lift()
            popup.focus_force()
        except Exception as exc:
            self._active_popups.discard(task.id)
            logger.exception("Failed to show reminder popup: %s", exc)

    # ── Task loading ──────────────────────────────────────────────────────────

    def load_tasks(self):
        """Fetch tasks from DB, sort, render cards, and schedule exact reminders."""
        rows = db.get_all_tasks()
        tasks = [Task.from_dict(r) for r in rows]
        tasks = self._sort_tasks(tasks)
        self._render_tasks(tasks)
        self._update_stats(tasks)
        # Schedule exact-time reminder jobs for upcoming tasks
        self._schedule_exact_for_tasks(tasks)

    def _sort_tasks(self, tasks: List[Task]) -> List[Task]:
        sort = self._sort_var.get()
        if sort == "Due Date":
            return sorted(tasks, key=lambda t: (t.due_datetime or "9999", t.completed))
        elif sort == "Priority":
            return sorted(tasks, key=lambda t: (PRIORITY_ORDER.get(t.priority, 3), t.completed))
        elif sort == "Created":
            return sorted(tasks, key=lambda t: t.created_at, reverse=True)
        elif sort == "Status":
            return sorted(tasks, key=lambda t: (t.completed, t.due_datetime or "9999"))
        return tasks

    def _render_tasks(self, tasks: List[Task]):
        # Clear existing cards
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()

        # Hide/show empty state
        if not tasks:
            self._scroll_frame.pack_forget()
            self._empty_frame.pack(fill="both", expand=True)
            return
        else:
            self._empty_frame.pack_forget()
            self._scroll_frame.pack(fill="both", expand=True, padx=20, pady=12)

        for task in tasks:
            card = TaskCard(
                self._scroll_frame,
                task=task,
                on_edit=self.show_edit_dialog,
                on_delete=self._handle_delete,
                on_complete=self._handle_complete,
            )
            card.pack(fill="x", padx=8, pady=6)

    def _update_stats(self, tasks: List[Task]):
        for w in self._stats_frame.winfo_children():
            w.destroy()

        total = len(tasks)
        done = sum(1 for t in tasks if t.completed)
        overdue = sum(1 for t in tasks if t.is_overdue())
        pending = total - done

        stats = [
            ("📋", "Total",   total,   C["text"]),
            ("⏳", "Pending", pending, C["accent"]),
            ("✅", "Done",    done,    C["success"]),
            ("🔴", "Overdue", overdue, C["priority_high"]),
        ]

        for icon, label, count, color in stats:
            chip = ctk.CTkFrame(
                self._stats_frame,
                fg_color=C["surface"],
                border_color=C["border"],
                border_width=1,
                corner_radius=12,
            )
            chip.pack(side="left", padx=(0, 12))
            ctk.CTkLabel(
                chip,
                text=f"  {icon}  {label}: {count}  ",
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                text_color=color,
            ).pack(padx=8, pady=6)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def show_add_dialog(self):
        TaskDialog(self, on_save=self._handle_add)

    def show_edit_dialog(self, task: Task):
        TaskDialog(self, on_save=self._handle_edit, task=task)

    def _handle_add(self, data: dict):
        db.create_task(
            title=data["title"],
            description=data.get("description", ""),
            due_datetime=data.get("due_datetime"),
            priority=data.get("priority", "Medium"),
        )
        logger.info("Task created: %r", data["title"])
        self.load_tasks()

    def _handle_edit(self, data: dict):
        db.update_task(
            task_id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            due_datetime=data.get("due_datetime"),
            priority=data.get("priority", "Medium"),
        )
        logger.info("Task updated id=%s", data["id"])
        self.load_tasks()

    def _handle_delete(self, task: Task):
        get_scheduler().cancel_exact(task.id)
        db.delete_task(task.id)
        logger.info("Task deleted id=%s", task.id)
        self.load_tasks()

    def _handle_complete(self, task: Task):
        was_completed = task.completed
        db.mark_complete(task.id, not was_completed)
        logger.info("Task id=%s completed=%s", task.id, not was_completed)
        self.load_tasks()
        if not was_completed:
            SuccessToast(self)

    # ── Graceful shutdown ─────────────────────────────────────────────────────

    def on_closing(self):
        get_scheduler().shutdown(wait=False)
        self.destroy()
