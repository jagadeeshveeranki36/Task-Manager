# ✅ Task Manager

> A modern, feature-rich desktop task management application built with Python and CustomTkinter.

**Made by Jagadeesh Veeranki**

---

## 📸 Overview

Task Manager is a sleek, fully-featured desktop productivity app that lets you create, manage, track, and get reminded about your tasks — all from a clean, glassmorphism-inspired UI. Built entirely in Python using CustomTkinter for a polished, modern look.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Create & Edit Tasks** | Add tasks with title, description, due date/time, and priority |
| **Priority Levels** | Set Low, Medium, or High priority with colour-coded badges |
| **Smart Reminders** | Background scheduler fires alerts when tasks become overdue |
| **⚠️ Task Alerts** | Prominent OS-style alert popup with snooze & complete actions |
| **Snooze Support** | Snooze reminders by 60 minutes with one click |
| **Sort & Filter** | Sort tasks by Due Date, Priority, Created, or Status |
| **Stats Dashboard** | Live counters for Total, Pending, Done, and Overdue tasks |
| **Completion Toast** | Auto-dismissing success toast when you complete a task |
| **Overdue Highlighting** | Cards with red border & OVERDUE badge for past-due tasks |
| **Delete Confirmation** | Safe delete flow with a confirmation dialog |
| **Persistent Storage** | All tasks saved locally in an SQLite database |
| **Rotating Logs** | Debug logs with 5 MB rotation and 3 backups |

---

## 🗂️ Project Structure

```
Task Manager/
├── main.py                  # Entry point — initialises logging & launches app
├── config.py                # Central config (paths, theme colours, window size)
├── logging_config.py        # Rotating file + console logging setup
├── requirements.txt         # Python dependencies
├── .gitignore
│
├── core/                    # Business logic layer
│   ├── __init__.py
│   ├── database.py          # SQLite CRUD operations
│   ├── models.py            # Task dataclass with helper properties
│   ├── scheduler.py         # APScheduler background reminder poller
│   └── notifications.py     # Desktop toast via plyer
│
└── ui/                      # Presentation layer (CustomTkinter)
    ├── __init__.py
    ├── app.py               # Main window, stats bar, task list
    ├── task_card.py         # Individual task card widget
    ├── add_edit_dialog.py   # Modal form for creating / editing tasks
    └── reminder_popup.py    # ⚠️ Alert-style reminder popup
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.11 or higher
- pip

### 1. Clone the repository
```bash
git clone https://github.com/jagadeesh-veeranki/task-manager.git
cd task-manager
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python main.py
```

---

## 🚀 Usage

1. **Add a task** — Click **＋ Add Task** in the toolbar
2. **Set details** — Enter title, description, due date/time, and priority
3. **Save** — Click 💾 Save Task
4. **Get reminded** — The app checks every 60 seconds; an alert pops up when tasks are overdue
5. **Complete / Snooze** — Use the reminder popup buttons or the checkbox on each card
6. **Edit / Delete** — Click the ⋮ menu on any task card

---

## 🗃️ Database

Tasks are stored in a local SQLite file at `tasks.db` (auto-created on first run). The schema:

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    description      TEXT DEFAULT '',
    due_datetime     TEXT,
    priority         TEXT DEFAULT 'Medium',
    completed        INTEGER DEFAULT 0,
    snoozed_until    TEXT,
    last_notified_at TEXT,
    created_at       TEXT NOT NULL
);
```

---

## 📋 Configuration

All configuration lives in `config.py`:

| Constant | Default | Description |
|---|---|---|
| `SCHEDULER_INTERVAL` | `60` | Seconds between reminder polls |
| `SNOOZE_MINUTES` | `60` | Minutes to snooze a reminder |
| `APP_TITLE` | `"Task Manager"` | Window title |
| `WINDOW_SIZE` | `"1050x700"` | Default window geometry |
| `MIN_WINDOW_SIZE` | `(860, 560)` | Minimum resizable size |

---

## 📝 Logging

Logs are written to `task_manager.log` with:
- **Rotating file handler** — 5 MB max, 3 backup files, UTF-8 encoded
- **Console handler** — INFO level and above printed to stdout

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "feat: add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 👤 Author

**Jagadeesh Veeranki**

- GitHub: [@jagadeesh-veeranki](https://github.com/jagadeesh-veeranki)

---

*Built with ❤️ using Python & CustomTkinter*
