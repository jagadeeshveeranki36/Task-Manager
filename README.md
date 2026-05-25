# ✅ Task Manager

> A modern desktop task management app built with Python and CustomTkinter — dark themed, glassmorphism-styled, and packed with smart reminders.

**Made by Jagadeesh Veeranki**

[![GitHub](https://img.shields.io/badge/GitHub-jagadeeshveeranki36-181717?style=for-the-badge&logo=github)](https://github.com/jagadeeshveeranki36/Task-Manager)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-7C3AED?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

## 📸 What is this?

Task Manager is a fully-featured desktop productivity app that I built in Python. You can create tasks, set due dates and priorities, and the app will alert you with a smooth popup when something is overdue — complete with snooze support, a live countdown, and auto-dismiss after 30 seconds.

It stores everything locally in an SQLite database, so your tasks are always there when you open it. No accounts, no cloud, no fuss.

---

## ✨ Features

| Feature | What it does |
|---|---|
| **Create & Edit Tasks** | Add a title, description, due date/time, and priority level |
| **Priority Levels** | Choose Low, Medium, or High — each gets a colour-coded badge |
| **Smart Reminders** | A background scheduler checks every 5 seconds and fires an alert when tasks are overdue |
| **Animated Alert Popup** | Slides in from centre, shakes for attention, auto-dismisses after 30 s |
| **Snooze Support** | Hit snooze on any reminder — it'll come back in 60 minutes |
| **Sort & Filter** | Sort your tasks by Due Date, Priority, Created, or Status |
| **Stats Bar** | Live counters at the top — Total, Pending, Done, and Overdue |
| **Completion Toast** | A little green toast pops up when you tick off a task |
| **Overdue Highlighting** | Past-due cards get a red border and an OVERDUE badge |
| **Safe Delete** | Asks for confirmation before removing any task |
| **Local SQLite Storage** | All data saved locally — no internet needed |
| **Rotating Logs** | Debug logs auto-rotate at 5 MB so they never pile up |

---

## 🗂️ Project Structure

```
Task Manager/
├── main.py                  # Entry point — sets up logging and starts the app
├── config.py                # All constants: colours, paths, window size, intervals
├── logging_config.py        # Rotating file + console log setup
├── requirements.txt         # Python dependencies
├── .gitignore
│
├── core/                    # Business logic
│   ├── __init__.py
│   ├── database.py          # SQLite CRUD (create, read, update, delete)
│   ├── models.py            # Task dataclass + helper methods (is_overdue, needs_reminder, etc.)
│   ├── scheduler.py         # APScheduler background poller + exact-time reminder jobs
│   └── notifications.py     # Desktop toast notifications via plyer
│
├── ui/                      # All the visual stuff (CustomTkinter)
│   ├── __init__.py
│   ├── app.py               # Main window, toolbar, stats bar, task list
│   ├── task_card.py         # Individual task card widget
│   ├── add_edit_dialog.py   # Modal form for creating and editing tasks
│   └── reminder_popup.py    # Animated alert popup with slide-in, shake, and countdown
│
└── web/                     # Standalone web version (HTML / CSS / JS)
    ├── index.html
    ├── style.css
    └── app.js
```

---

## ⚙️ Setup & Installation

You'll need **Python 3.11 or higher** and **pip**.

### 1. Clone the repo

```bash
git clone https://github.com/jagadeeshveeranki36/Task-Manager.git
cd Task-Manager
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

### 4. Run the app

```bash
python main.py
```

The database (`tasks.db`) and log file (`task_manager.log`) are created automatically on first run — you don't need to set anything up manually.

---

## 🚀 How to use it

1. **Add a task** — Click **＋ Add Task** in the top toolbar
2. **Fill in the details** — Title (required), description, due date, time, and priority
3. **Save it** — Click 💾 Save Task
4. **Get reminded** — When a task becomes overdue, a popup slides in automatically
5. **Act on it** — Mark it done, snooze it for 60 minutes, or dismiss the alert
6. **Edit or delete** — Click the ⋮ menu on any task card

---

## 🗃️ Database Schema

Tasks are stored in `tasks.db` (auto-created in the project root). Here's the schema:

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

Everything is controlled from `config.py` — no digging through code:

| Constant | Value | What it controls |
|---|---|---|
| `SCHEDULER_INTERVAL` | `5` | Seconds between reminder polls |
| `NOTIFICATION_COOLDOWN` | `300` | Seconds before re-alerting the same task (5 min) |
| `SNOOZE_MINUTES` | `60` | How long a snooze lasts |
| `APP_TITLE` | `"Task Manager"` | Window title bar text |
| `WINDOW_SIZE` | `"1050x700"` | Default window size |
| `MIN_WINDOW_SIZE` | `(860, 560)` | Minimum resize limit |

---

## 📝 Logging

Logs are written to `task_manager.log` in the project root:

- **File handler** — rotates at 5 MB, keeps 3 backups, UTF-8 encoded
- **Console handler** — shows INFO and above in your terminal

Both the log file and database are listed in `.gitignore` so they're never accidentally committed.

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repo
2. Create a feature branch — `git checkout -b feature/your-feature`
3. Make your changes and commit — `git commit -m "feat: describe your change"`
4. Push to your fork — `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is open source under the [MIT License](LICENSE).

---

## 👤 Author

**Jagadeesh Veeranki**

- GitHub: [@jagadeeshveeranki36](https://github.com/jagadeeshveeranki36)

---

*Built with ❤️ using Python & CustomTkinter*
