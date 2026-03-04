"""Central configuration for the Task Manager application."""

import os

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tasks.db")
LOG_PATH = os.path.join(BASE_DIR, "task_manager.log")

# ── Scheduler ─────────────────────────────────────────────────────────────────
SCHEDULER_INTERVAL = 60        # seconds between reminder polls
SNOOZE_MINUTES = 60            # minutes to snooze a reminder

# ── Theme ─────────────────────────────────────────────────────────────────────
THEME_COLORS = {
    # Base
    "bg":              "#F5FAF5",      # very light green-tinted white
    "surface":         "#FFFFFF",      # card surface
    "border":          "#D4EDD4",      # subtle green border

    # Brand greens
    "primary":         "#2ECC71",      # main accent green
    "primary_dark":    "#27AE60",      # hover / pressed
    "primary_light":   "#A9DFBF",      # soft accent
    "primary_glow":    "#D5F5E3",      # glass shimmer

    # Text
    "text":            "#1A2E1A",      # dark green-black
    "text_secondary":  "#5D7A5D",      # muted label
    "text_muted":      "#9BB49B",      # placeholder / disabled

    # Priority badges
    "priority_low":    "#7F8C8D",      # grey
    "priority_medium": "#E67E22",      # amber
    "priority_high":   "#E74C3C",      # red

    # States
    "overdue_border":  "#E74C3C",      # red glow for overdue cards
    "completed_bg":    "#F0FFF0",      # faint green for completed
    "success":         "#2ECC71",      # success popup accent

    # Toolbar / sidebar
    "toolbar":         "#FFFFFF",
    "toolbar_border":  "#C8E6C9",

    # Buttons
    "btn_primary":     "#2ECC71",
    "btn_primary_fg":  "#FFFFFF",
    "btn_danger":      "#E74C3C",
    "btn_danger_fg":   "#FFFFFF",
}

# ── Window ────────────────────────────────────────────────────────────────────
APP_TITLE = "Task Manager"
WINDOW_SIZE = "1050x700"
MIN_WINDOW_SIZE = (860, 560)
