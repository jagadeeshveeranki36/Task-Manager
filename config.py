"""Central configuration for the Task Manager application.

Author: Jagadeesh Veeranki
"""

import os

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tasks.db")
LOG_PATH = os.path.join(BASE_DIR, "task_manager.log")

# ── Scheduler ─────────────────────────────────────────────────────────────────
SCHEDULER_INTERVAL = 5         # seconds between reminder polls (keep small for accuracy)
NOTIFICATION_COOLDOWN = 300   # seconds before re-notifying the same task (5 min)
SNOOZE_MINUTES = 60            # minutes to snooze a reminder

# ── Theme ─────────────────────────────────────────────────────────────────────
THEME_COLORS = {
    # ── Base ─────────────────────────────────────────────────────────
    "bg":              "#0F1117",      # deep space navy (main background)
    "surface":         "#1A1D2E",      # card/surface — slightly lighter navy
    "surface_2":       "#22263A",      # elevated surface (toolbar, dialogs)
    "border":          "#2E3357",      # subtle indigo border

    # ── Brand — Electric Violet / Indigo ─────────────────────────────
    "primary":         "#7C3AED",      # electric violet
    "primary_dark":    "#6D28D9",      # deep violet (hover/pressed)
    "primary_light":   "#A78BFA",      # soft lavender
    "primary_glow":    "#1E1535",      # very dark violet tint (button bg)

    # ── Accent — Vibrant Teal ─────────────────────────────────────────
    "accent":          "#06B6D4",      # cyan-teal
    "accent_dark":     "#0891B2",      # darker teal
    "accent_glow":     "#0E2A35",      # dark teal tint

    # ── Text ─────────────────────────────────────────────────────────
    "text":            "#F1F5F9",      # near-white (primary text)
    "text_secondary":  "#94A3B8",      # slate grey (labels)
    "text_muted":      "#475569",      # dim (disabled / placeholder)

    # ── Priority badges ───────────────────────────────────────────────
    "priority_low":    "#22C55E",      # vivid green
    "priority_medium": "#F59E0B",      # amber
    "priority_high":   "#EF4444",      # vivid red

    # ── States ────────────────────────────────────────────────────────
    "overdue_border":  "#EF4444",      # red glow for overdue cards
    "completed_bg":    "#12172A",      # faint dark blue for completed
    "success":         "#10B981",      # emerald success

    # ── Toolbar / sidebar ─────────────────────────────────────────────
    "toolbar":         "#13162A",
    "toolbar_border":  "#2E3357",

    # ── Buttons ───────────────────────────────────────────────────────
    "btn_primary":     "#7C3AED",
    "btn_primary_fg":  "#FFFFFF",
    "btn_danger":      "#EF4444",
    "btn_danger_fg":   "#FFFFFF",
}

# ── Window ────────────────────────────────────────────────────────────────────
APP_TITLE = "Task Manager"
WINDOW_SIZE = "1050x700"
MIN_WINDOW_SIZE = (860, 560)
