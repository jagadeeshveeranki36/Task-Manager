"""Add/Edit Task dialog — CustomTkinter modal form."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime
from typing import Optional, Callable

from config import THEME_COLORS
from core.models import Task

logger = logging.getLogger(__name__)

C = THEME_COLORS


class TaskDialog(ctk.CTkToplevel):
    """Modal dialog for adding or editing a task."""

    def __init__(
        self,
        parent,
        on_save: Callable[[dict], None],
        task: Optional[Task] = None,
    ):
        super().__init__(parent)
        self._on_save = on_save
        self._task = task
        self._is_edit = task is not None

        self.title("Edit Task" if self._is_edit else "New Task")
        self.resizable(False, False)
        self.grab_set()
        self.focus_force()

        self._build_ui()
        self._center(parent)

        if self._is_edit:
            self._populate(task)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.configure(fg_color=C["surface_2"])

        wrapper = ctk.CTkFrame(self, fg_color=C["surface_2"], corner_radius=0)
        wrapper.pack(fill="both", expand=True, padx=30, pady=24)

        # Header
        header_lbl = ctk.CTkLabel(
            wrapper,
            text="✏️  Edit Task" if self._is_edit else "➕  New Task",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=C["text"],
        )
        header_lbl.pack(anchor="w", pady=(0, 20))

        # Title
        self._add_label(wrapper, "Task Title *")
        self._title_var = ctk.StringVar()
        self._title_entry = ctk.CTkEntry(
            wrapper,
            textvariable=self._title_var,
            placeholder_text="What do you need to do?",
            width=420,
            height=40,
            corner_radius=10,
            border_color=C["border"],
            fg_color=C["surface"],
            text_color=C["text"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self._title_entry.pack(fill="x", pady=(0, 14))
        self._title_entry.focus()

        # Description
        self._add_label(wrapper, "Description (optional)")
        self._desc_box = ctk.CTkTextbox(
            wrapper,
            width=420,
            height=80,
            corner_radius=10,
            border_color=C["border"],
            border_width=1,
            fg_color=C["surface"],
            text_color=C["text"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self._desc_box.pack(fill="x", pady=(0, 14))

        # Date + Time row
        dt_row = ctk.CTkFrame(wrapper, fg_color="transparent")
        dt_row.pack(fill="x", pady=(0, 14))

        date_col = ctk.CTkFrame(dt_row, fg_color="transparent")
        date_col.pack(side="left", expand=True, fill="x", padx=(0, 10))
        self._add_label(date_col, "Date")
        self._date_entry = DateEntry(
            date_col,
            width=14,
            background="#7C3AED",
            foreground="white",
            borderwidth=0,
            date_pattern="yyyy-mm-dd",
            font=("Segoe UI", 12),
        )
        self._date_entry.pack(fill="x", ipady=6)

        time_col = ctk.CTkFrame(dt_row, fg_color="transparent")
        time_col.pack(side="left", expand=True, fill="x")
        self._add_label(time_col, "Time (HH : MM)")

        time_inner = ctk.CTkFrame(time_col, fg_color="transparent")
        time_inner.pack(fill="x")

        self._hour_var = ctk.StringVar(value="09")
        self._min_var = ctk.StringVar(value="00")

        self._hour_spin = ctk.CTkEntry(
            time_inner, textvariable=self._hour_var, width=60, height=36,
            corner_radius=8, fg_color=C["surface"], text_color=C["text"],
            border_color=C["border"], font=ctk.CTkFont("Segoe UI", 13),
            justify="center",
        )
        self._hour_spin.pack(side="left")

        ctk.CTkLabel(time_inner, text=":", text_color=C["text"],
                     font=ctk.CTkFont("Segoe UI", 16, "bold")).pack(side="left", padx=4)

        self._min_spin = ctk.CTkEntry(
            time_inner, textvariable=self._min_var, width=60, height=36,
            corner_radius=8, fg_color=C["surface"], text_color=C["text"],
            border_color=C["border"], font=ctk.CTkFont("Segoe UI", 13),
            justify="center",
        )
        self._min_spin.pack(side="left")

        # Priority
        self._add_label(wrapper, "Priority")
        self._priority_var = ctk.StringVar(value="Medium")
        self._priority_seg = ctk.CTkSegmentedButton(
            wrapper,
            values=["Low", "Medium", "High"],
            variable=self._priority_var,
            selected_color=C["primary"],
            selected_hover_color=C["primary_dark"],
            fg_color=C["surface"],
            text_color=C["text"],
            font=ctk.CTkFont("Segoe UI", 13),
            height=36,
            corner_radius=10,
        )
        self._priority_seg.pack(fill="x", pady=(0, 20))

        # Buttons
        btn_row = ctk.CTkFrame(wrapper, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=90,
            height=38,
            corner_radius=10,
            fg_color=C["primary_glow"],
            hover_color=C["border"],
            text_color=C["text"],
            font=ctk.CTkFont("Segoe UI", 13),
            command=self.destroy,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row,
            text="💾  Save Task",
            width=140,
            height=38,
            corner_radius=10,
            fg_color=C["btn_primary"],
            hover_color=C["primary_dark"],
            text_color=C["btn_primary_fg"],
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            command=self._save,
        ).pack(side="right")

    def _add_label(self, parent, text: str):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=C["text_secondary"],
        ).pack(anchor="w", pady=(0, 4))

    # ── Populate (edit mode) ───────────────────────────────────────────────────

    def _populate(self, task: Task):
        self._title_var.set(task.title)
        self._desc_box.insert("1.0", task.description or "")
        if task.due_dt:
            try:
                self._date_entry.set_date(task.due_dt.date())
                self._hour_var.set(f"{task.due_dt.hour:02d}")
                self._min_var.set(f"{task.due_dt.minute:02d}")
            except Exception:
                pass
        self._priority_var.set(task.priority or "Medium")

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self):
        title = self._title_var.get().strip()
        if not title:
            messagebox.showwarning("Missing Title", "Please enter a task title.", parent=self)
            self._title_entry.focus()
            return

        # Validate hour / minute
        try:
            h = int(self._hour_var.get())
            m = int(self._min_var.get())
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Time",
                                   "Hour must be 00-23 and minute must be 00-59.", parent=self)
            return

        date_str = self._date_entry.get_date().isoformat()
        due_datetime = f"{date_str}T{h:02d}:{m:02d}:00"

        data = {
            "title": title,
            "description": self._desc_box.get("1.0", "end-1c").strip(),
            "due_datetime": due_datetime,
            "priority": self._priority_var.get(),
        }
        if self._is_edit:
            data["id"] = self._task.id

        logger.debug("TaskDialog saving: %s", data)
        self._on_save(data)
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
