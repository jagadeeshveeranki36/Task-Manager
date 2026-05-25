"""Entry point for the Task Manager application.

Author: Jagadeesh Veeranki
"""

import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logging_config import setup_logging

# Initialise logging before any other import
setup_logging()

from config import BASE_DIR
from core.database import init_db
from ui.app import App


def main():
    init_db()

    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)

    # Set professional app icon
    icon_path = os.path.join(BASE_DIR, "assets", "icon.ico")
    if os.path.exists(icon_path):
        try:
            app.iconbitmap(icon_path)
        except Exception:
            pass  # non-critical

    app.mainloop()


if __name__ == "__main__":
    main()
