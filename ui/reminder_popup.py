"""Apple-style reminder popup for Task Manager.

Design goals
------------
* Slides in from slightly below its final position (smooth, like macOS notifications)
* Shakes left/right when first shown to grab attention
* Live countdown label updates every second
* Auto-dismisses after 30 s with an animated progress bar
* Forces itself in front of any other application via ctypes
* Translucent dark backdrop behind the card
"""

import sys
import os
import ctypes
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk
import tkinter as tk

from config import THEME_COLORS, SNOOZE_MINUTES
from core.models import Task
from core import database as db

logger = logging.getLogger(__name__)

C = THEME_COLORS

# ─── palette ──────────────────────────────────────────────────────────────────
_WHITE      = "#FFFFFF"
_BG_CARD    = "#1A1D2E"          # dark navy card
_ACCENT     = "#7C3AED"          # electric violet
_ACCENT_D   = "#6D28D9"
_TEXT       = "#F1F5F9"          # near-white
_TEXT_SUB   = "#94A3B8"          # slate grey
_OVERDUE    = "#EF4444"          # vivid red
_DUE_OK     = "#06B6D4"          # teal
_BACKDROP   = "#000000"
_SHADOW     = "#0A0C18"          # very dark navy shadow

_SLIDE_DIST = 40   # px the card travels on slide-in
_SHAKE_AMT  = 10   # px for shake animation
_AUTO_CLOSE_MS = 30_000   # 30 s


def _force_foreground(hwnd: int) -> None:
    """Use ctypes to bring a window to the foreground on Windows."""
    try:
        ctypes.windll.user32.ShowWindow(hwnd, 9)          # SW_RESTORE
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        ctypes.windll.user32.BringWindowToTop(hwnd)
        ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
    except Exception:
        pass


class ReminderPopup(ctk.CTkToplevel):
    """Apple-style fullscreen-overlay reminder popup."""

    def __init__(
        self,
        parent,
        task: Task,
        on_complete: Optional[Callable[[Task], None]] = None,
        on_dismiss: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self._task = task
        self._on_complete = on_complete
        self._on_dismiss = on_dismiss
        self._remaining_ms = _AUTO_CLOSE_MS
        self._dismissed = False

        # ── Window chrome ──────────────────────────────────────────────────
        self.title("")
        self.resizable(False, False)
        self.overrideredirect(True)          # borderless
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)       # start invisible for fade-in

        self._build_ui()
        self._place_center(parent)

        # Force on top of everything else on Windows
        self.update_idletasks()
        self.after(50, lambda: _force_foreground(self.winfo_id()))

        # Kick off animations
        self.after(80, self._slide_in)

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self):
        # Outer shell — drop-shadow simulation via a slightly-offset dark frame
        shadow = ctk.CTkFrame(self, fg_color=_SHADOW, corner_radius=24)
        shadow.place(x=4, y=6, relwidth=1.0, relheight=1.0)

        # Main card
        card = ctk.CTkFrame(
            self,
            fg_color=_BG_CARD,
            corner_radius=22,
        )
        card.pack(fill="both", expand=True, padx=2, pady=2)

        # ── Top accent line ────────────────────────────────────────────────
        ctk.CTkFrame(card, fg_color=_ACCENT, height=4, corner_radius=2).pack(
            fill="x", padx=20, pady=(14, 0)
        )

        # ── Icon ───────────────────────────────────────────────────────────
        ctk.CTkLabel(
            card,
            text="🔔",
            font=ctk.CTkFont(size=52),
        ).pack(pady=(12, 0))

        # ── Header: "TASK DUE" ─────────────────────────────────────────────
        ctk.CTkLabel(
            card,
            text="⚠  TASK DUE  ⚠",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=_TEXT_SUB,
        ).pack(pady=(4, 0))

        # ── Task title ─────────────────────────────────────────────────────
        ctk.CTkLabel(
            card,
            text=self._task.title,
            font=ctk.CTkFont("Segoe UI", 19, "bold"),
            text_color=_TEXT,
            wraplength=310,
            justify="center",
        ).pack(padx=24, pady=(8, 0))

        # ── Countdown label ────────────────────────────────────────────────
        self._countdown_label = ctk.CTkLabel(
            card,
            text=self._countdown_text(),
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=_TEXT_SUB,
        )
        self._countdown_label.pack(pady=(4, 0))

        # ── Due time & priority row ────────────────────────────────────────
        meta_row = ctk.CTkFrame(card, fg_color="transparent")
        meta_row.pack(pady=(6, 0))

        if self._task.due_dt:
            ctk.CTkLabel(
                meta_row,
                text=f"🕐 {self._task.due_dt.strftime('%d %b · %I:%M %p')}",
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=_TEXT_SUB,
            ).pack(side="left", padx=(0, 12))

        prio_colors = {"High": "#FF3B30", "Medium": "#FF9500", "Low": "#8E8E93"}
        pcolor = prio_colors.get(self._task.priority, "#8E8E93")
        ctk.CTkLabel(
            meta_row,
            text=f"  {self._task.priority}  ",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=_WHITE,
            fg_color=pcolor,
            corner_radius=8,
        ).pack(side="left")

        # ── Separator ─────────────────────────────────────────────────────
        ctk.CTkFrame(card, fg_color="#E5E5EA", height=1).pack(
            fill="x", padx=20, pady=(14, 0)
        )

        # ── Action buttons ─────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(10, 0))

        ctk.CTkButton(
            btn_row,
            text="✓  Done",
            height=44,
            corner_radius=14,
            fg_color=_ACCENT,
            hover_color=_ACCENT_D,
            text_color=_WHITE,
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            command=self._action_complete,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btn_row,
            text=f"💤  {SNOOZE_MINUTES}m",
            height=44,
            corner_radius=14,
            fg_color=C["surface"],
            hover_color=C["border"],
            text_color=C["text"],
            font=ctk.CTkFont("Segoe UI", 14),
            command=self._action_snooze,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btn_row,
            text="✕",
            height=44,
            width=44,
            corner_radius=14,
            fg_color=C["surface"],
            hover_color=C["border"],
            text_color=C["text_secondary"],
            font=ctk.CTkFont("Segoe UI", 14),
            command=self._action_dismiss,
        ).pack(side="left")

        # ── Auto-dismiss progress bar ─────────────────────────────────────
        progress_track = ctk.CTkFrame(card, fg_color=C["border"], height=3, corner_radius=2)
        progress_track.pack(fill="x", padx=20, pady=(12, 16))

        self._progress_bar = ctk.CTkFrame(
            progress_track,
            fg_color=_ACCENT,
            height=3,
            corner_radius=2,
        )
        self._progress_bar.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)

        # Start live update loops
        self.after(1000, self._tick)
        self.after(50, self._update_progress)

    # ── Placement ─────────────────────────────────────────────────────────

    def _place_center(self, parent):
        self.update_idletasks()
        w = 370
        h = self.winfo_reqheight()

        # Try to get screen dimensions
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        x = (sw - w) // 2
        y = (sh - h) // 2

        self._final_x = x
        self._final_y = y
        self._slide_y = y + _SLIDE_DIST

        self.geometry(f"{w}x{h}+{x}+{self._slide_y}")

    # ── Animations ────────────────────────────────────────────────────────

    def _slide_in(self, step: int = 0):
        """Smooth slide-up + fade-in over ~300 ms."""
        steps = 12
        if step > steps or self._dismissed:
            # Position exactly and then shake
            self.geometry(f"+{self._final_x}+{self._final_y}")
            self.attributes("-alpha", 1.0)
            self.after(50, lambda: self._shake(6))
            return

        frac = step / steps
        # ease-out cubic
        ease = 1 - (1 - frac) ** 3
        cur_y = int(self._slide_y - _SLIDE_DIST * ease)
        alpha = min(1.0, ease * 1.3)
        self.geometry(f"+{self._final_x}+{cur_y}")
        self.attributes("-alpha", alpha)
        self.after(20, lambda: self._slide_in(step + 1))

    def _shake(self, times: int, phase: int = 0):
        """Shake the card left/right for attention."""
        if times <= 0 or self._dismissed:
            self.geometry(f"+{self._final_x}+{self._final_y}")
            return
        offsets = [_SHAKE_AMT, -_SHAKE_AMT, _SHAKE_AMT // 2, -_SHAKE_AMT // 2, 0]
        ox = offsets[phase % len(offsets)]
        self.geometry(f"+{self._final_x + ox}+{self._final_y}")
        self.after(45, lambda: self._shake(times - 1, phase + 1))

    def _update_progress(self):
        """Shrink the green progress bar as auto-close time approaches."""
        if self._dismissed:
            return
        frac = max(0.0, self._remaining_ms / _AUTO_CLOSE_MS)
        try:
            self._progress_bar.place(relx=0, rely=0, relwidth=frac, relheight=1.0)
        except Exception:
            return
        self.after(100, self._update_progress)

    def _tick(self):
        """Update countdown label + auto-dismiss timer every second."""
        if self._dismissed:
            return
        self._remaining_ms -= 1000
        if self._remaining_ms <= 0:
            self._action_dismiss()
            return
        try:
            self._countdown_label.configure(text=self._countdown_text())
        except Exception:
            return
        self.after(1000, self._tick)

    def _countdown_text(self) -> str:
        if not self._task.due_dt:
            return ""
        now = datetime.now()
        delta = (self._task.due_dt - now).total_seconds()
        if delta > 0:
            m, s = divmod(int(delta), 60)
            h, m = divmod(m, 60)
            if h:
                return f"Due in {h}h {m}m"
            elif m:
                return f"Due in {m}m {s}s"
            else:
                return f"Due in {s}s"
        else:
            delta = abs(delta)
            m, s = divmod(int(delta), 60)
            h, m = divmod(m, 60)
            if h:
                return f"Overdue by {h}h {m}m"
            elif m:
                return f"Overdue by {m}m {s}s"
            else:
                return f"Overdue by {s}s"

    # ── Actions ───────────────────────────────────────────────────────────

    def _action_complete(self):
        db.mark_complete(self._task.id, True)
        self._task.completed = True
        logger.info("Task %s marked complete from reminder popup", self._task.id)
        if self._on_complete:
            self._on_complete(self._task)
        self._close()

    def _action_snooze(self):
        snooze_dt = (datetime.now() + timedelta(minutes=SNOOZE_MINUTES)).isoformat(
            timespec="seconds"
        )
        db.set_snoozed_until(self._task.id, snooze_dt)
        logger.info("Task %s snoozed until %s", self._task.id, snooze_dt)
        self._close()

    def _action_dismiss(self):
        db.set_last_notified(self._task.id)
        logger.info("Task %s reminder dismissed", self._task.id)
        self._close()

    def _close(self):
        self._dismissed = True
        # Notify the caller so it can clean up (e.g. remove from active_popups)
        if self._on_dismiss:
            try:
                self._on_dismiss()
            except Exception:
                pass
        # Fade out
        self._fade_out(10)

    def _fade_out(self, steps: int):
        if steps <= 0:
            try:
                self.destroy()
            except Exception:
                pass
            return
        alpha = max(0.0, steps / 10)
        try:
            self.attributes("-alpha", alpha)
        except Exception:
            return
        self.after(18, lambda: self._fade_out(steps - 1))
