from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

from app.db.database import init_db


ROOT = Path(__file__).resolve().parent


def main() -> None:
    load_dotenv(ROOT / ".env")
    (ROOT / "data").mkdir(exist_ok=True)
    init_db(ROOT / "data" / "storymemory.sqlite3")
    app_path = ROOT / "app" / "ui" / "streamlit_app.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        "127.0.0.1",
        "--server.port",
        "8501",
        "--client.showSidebarNavigation",
        "false",
        "--browser.gatherUsageStats",
        "false",
    ]
    subprocess.run(cmd, cwd=ROOT, check=False)


if __name__ == "__main__":
    main()
