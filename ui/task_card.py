"""Individual Task Card widget with glassmorphism styling."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import tkinter as tk
from datetime import datetime
from typing import Callable, Optional

import customtkinter as ctk

from config import THEME_COLORS
from core.models import Task

logger = logging.getLogger(__name__)

C = THEME_COLORS

PRIORITY_BADGE = {
    "High":   (C["priority_high"],   "🔴"),
    "Medium": (C["priority_medium"], "🟡"),
    "Low":    (C["priority_low"],    "⚪"),
}


class TaskCard(ctk.CTkFrame):
    """Glassmorphism-style card representing a single task."""

    def __init__(
        self,
        master,
        task: Task,
        on_edit: Callable[[Task], None],
        on_delete: Callable[[Task], None],
        on_complete: Callable[[Task], None],
        **kwargs,
    ):
        border_color = C["overdue_border"] if (task.is_overdue()) else C["border"]
        bg = C["completed_bg"] if task.completed else C["surface"]

        super().__init__(
            master,
            fg_color=bg,
            border_color=border_color,
            border_width=2 if task.is_overdue() else 1,
            corner_radius=16,
            **kwargs,
        )
        self._task = task
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._on_complete = on_complete

        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        task = self._task

        # Outer padding frame
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=16, pady=12)

        # ── Top row: checkbox + title + menu ──────────────────────────────────
        top = ctk.CTkFrame(outer, fg_color="transparent")
        top.pack(fill="x")

        # Checkbox
        self._check_var = ctk.BooleanVar(value=task.completed)
        check = ctk.CTkCheckBox(
            top,
            text="",
            variable=self._check_var,
            width=24,
            height=24,
            checkbox_width=22,
            checkbox_height=22,
            corner_radius=6,
            fg_color=C["primary"],
            hover_color=C["primary_dark"],
            border_color=C["border"],
            command=self._toggle_complete,
        )
        check.pack(side="left", padx=(0, 10))

        # Title
        title_font = ctk.CTkFont("Segoe UI", 14, "bold")
        title_color = C["text_muted"] if task.completed else C["text"]
        self._title_lbl = ctk.CTkLabel(
            top,
            text=task.title,
            font=title_font,
            text_color=title_color,
            anchor="w",
        )
        self._title_lbl.pack(side="left", fill="x", expand=True)

        # Overdue tag
        if task.is_overdue():
            ctk.CTkLabel(
                top,
                text="  OVERDUE  ",
                fg_color=C["priority_high"],
                text_color="white",
                corner_radius=6,
                font=ctk.CTkFont("Segoe UI", 10, "bold"),
            ).pack(side="left", padx=(6, 6))

        # ⋮ menu button
        menu_btn = ctk.CTkButton(
            top,
            text="⋮",
            width=30,
            height=30,
            corner_radius=8,
            fg_color="transparent",
            hover_color=C["primary_glow"],
            text_color=C["text_secondary"],
            font=ctk.CTkFont("Segoe UI", 18),
            command=self._show_menu,
        )
        menu_btn.pack(side="right")

        # ── Description ───────────────────────────────────────────────────────
        desc = (task.description or "").strip()
        if desc:
            desc_preview = desc[:90] + "…" if len(desc) > 90 else desc
            ctk.CTkLabel(
                outer,
                text=desc_preview,
                font=ctk.CTkFont("Segoe UI", 12),
                text_color=C["text_muted"],
                anchor="w",
                justify="left",
                wraplength=550,
            ).pack(fill="x", pady=(4, 0))

        # ── Bottom row: due date/time + priority badge ─────────────────────────
        bottom = ctk.CTkFrame(outer, fg_color="transparent")
        bottom.pack(fill="x", pady=(8, 0))

        # Due datetime
        if task.due_dt:
            due_str = task.due_dt.strftime("%d %b %Y  %H:%M")
            clock_color = C["priority_high"] if task.is_overdue() else C["text_secondary"]
            ctk.CTkLabel(
                bottom,
                text=f"🕐  {due_str}",
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=clock_color,
                anchor="w",
            ).pack(side="left")

        # Priority badge
        prio_color, prio_icon = PRIORITY_BADGE.get(
            task.priority, (C["priority_low"], "⚪")
        )
        ctk.CTkLabel(
            bottom,
            text=f"  {prio_icon}  {task.priority}  ",
            fg_color=prio_color,
            text_color="#FFFFFF",
            corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
        ).pack(side="right")

        # Completed stamp
        if task.completed:
            ctk.CTkLabel(
                bottom,
                text="  ✅ Completed  ",
                fg_color=C["primary"],
                text_color="white",
                corner_radius=8,
                font=ctk.CTkFont("Segoe UI", 11, "bold"),
            ).pack(side="right", padx=(0, 8))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _toggle_complete(self):
        self._on_complete(self._task)

    def _show_menu(self):
        menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 11))
        menu.add_command(label="✏️  Edit", command=lambda: self._on_edit(self._task))
        menu.add_separator()
        menu.add_command(label="🗑️  Delete", command=self._confirm_delete)
        try:
            menu.tk_popup(
                self.winfo_rootx() + self.winfo_width() - 40,
                self.winfo_rooty() + 30,
            )
        finally:
            menu.grab_release()

    def _confirm_delete(self):
        """Show confirmation dialog before deleting."""
        confirm = ctk.CTkToplevel(self)
        confirm.title("Confirm Delete")
        confirm.resizable(False, False)
        confirm.grab_set()
        confirm.attributes("-topmost", True)
        confirm.focus_force()
        confirm.configure(fg_color=C["surface"])

        frame = ctk.CTkFrame(confirm, fg_color="transparent")
        frame.pack(padx=28, pady=24)

        ctk.CTkLabel(
            frame,
            text="🗑️  Delete Task?",
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            text_color=C["text"],
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            frame,
            text=f'Are you sure you want to delete\n"{self._task.title}"?',
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=C["text_secondary"],
            justify="center",
            wraplength=280,
        ).pack(pady=(0, 20))

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack()

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=90,
            height=36,
            corner_radius=10,
            fg_color=C["primary_glow"],
            hover_color=C["border"],
            text_color=C["text"],
            command=confirm.destroy,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row,
            text="Delete",
            width=90,
            height=36,
            corner_radius=10,
            fg_color=C["btn_danger"],
            hover_color="#C0392B",
            text_color="white",
            command=lambda: [confirm.destroy(), self._on_delete(self._task)],
        ).pack(side="left")

        # Centre over parent window
        confirm.update_idletasks()
        root = self.winfo_toplevel()
        x = root.winfo_rootx() + (root.winfo_width() - confirm.winfo_reqwidth()) // 2
        y = root.winfo_rooty() + (root.winfo_height() - confirm.winfo_reqheight()) // 2
        confirm.geometry(f"+{x}+{y}")
