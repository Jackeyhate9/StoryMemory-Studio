from __future__ import annotations

import atexit
import os
import shutil
import socket
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

from dotenv import load_dotenv


APP_NAME = "StoryMemory Studio"


def runtime_dir() -> Path:
    """Directory beside the exe. User data must live here, not in _MEIPASS."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_dir() -> Path:
    """Directory containing bundled app resources."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


def log_path() -> Path:
    return runtime_dir() / "start_log.txt"


def write_log(message: str) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def show_error(message: str) -> None:
    write_log(message)
    try:
        import tkinter.messagebox as messagebox

        messagebox.showerror(APP_NAME, f"{message}\n\n详情请查看 start_log.txt")
    except Exception:
        pass


def ensure_env_file(root: Path, resources: Path) -> Path:
    env_path = root / ".env"
    example_in_root = root / ".env.example"
    example_in_bundle = resources / ".env.example"
    if not example_in_root.exists() and example_in_bundle.exists():
        shutil.copy2(example_in_bundle, example_in_root)
    if not env_path.exists():
        if example_in_root.exists():
            shutil.copy2(example_in_root, env_path)
        else:
            env_path.write_text(
                "\n".join(
                    [
                        "DEEPSEEK_API_KEY=",
                        "DEEPSEEK_BASE_URL=https://api.deepseek.com",
                        "OPENAI_COMPATIBLE_API_KEY=",
                        "OPENAI_COMPATIBLE_BASE_URL=",
                        "OLLAMA_BASE_URL=http://127.0.0.1:11434",
                        "DEFAULT_MODEL_PROVIDER=ollama",
                        "DEFAULT_OLLAMA_MODEL=auto",
                        "STORYMEMORY_DATA_DIR=./data",
                        "STORYMEMORY_EXPORT_DIR=./exports",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
    return env_path


def find_free_port(start: int = 8501, end: int = 8599) -> int:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("没有找到可用端口，请关闭占用 8501-8599 的本地程序后重试。")


def prepare_runtime() -> tuple[Path, Path]:
    root = runtime_dir()
    resources = resource_dir()
    root.mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(exist_ok=True)
    (root / "exports").mkdir(exist_ok=True)
    (root / "logs").mkdir(exist_ok=True)
    os.environ["STORYMEMORY_RUNTIME_DIR"] = str(root)
    os.environ["STORYMEMORY_RESOURCE_DIR"] = str(resources)
    os.environ.setdefault("STORYMEMORY_DB_PATH", str(root / "data" / "storymemory.sqlite3"))
    os.environ.setdefault("STORYMEMORY_EXPORT_DIR", str(root / "exports"))
    os.environ.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    os.environ.setdefault("DEFAULT_MODEL_PROVIDER", "ollama")
    os.environ.setdefault("DEFAULT_OLLAMA_MODEL", "auto")
    sys.path.insert(0, str(resources))
    os.chdir(root)
    return root, resources


def check_ollama() -> str:
    host = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    host = host.replace("http://", "").replace("https://", "").split("/")[0]
    if ":" not in host:
        return "未检测：OLLAMA_BASE_URL 缺少端口"
    address, port_text = host.rsplit(":", 1)
    try:
        port = int(port_text)
    except ValueError:
        return "未检测：OLLAMA_BASE_URL 端口无效"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        ok = sock.connect_ex((address, port)) == 0
    return "可用" if ok else "未连接，可在设置页配置云端 API 或启动 Ollama"


def initialize_database() -> None:
    from app.config import get_settings
    from app.db.database import init_db

    get_settings.cache_clear()
    db_path = Path(os.environ["STORYMEMORY_DB_PATH"])
    init_db(db_path)
    write_log(f"数据库已初始化：{db_path}")


def main() -> None:
    try:
        root, resources = prepare_runtime()
        log_path().write_text("", encoding="utf-8-sig")
        write_log(f"{APP_NAME} 启动")
        write_log(f"运行目录：{root}")
        write_log(f"资源目录：{resources}")

        env_path = ensure_env_file(root, resources)
        load_dotenv(env_path, override=False)
        initialize_database()
        write_log(f"Ollama 状态：{check_ollama()}")

        app_path = resources / "app" / "ui" / "streamlit_app.py"
        if not app_path.exists():
            raise FileNotFoundError(f"找不到 Streamlit 入口：{app_path}")

        port = find_free_port()
        url = f"http://127.0.0.1:{port}"
        write_log(f"前端地址：{url}")

        def open_browser() -> None:
            try:
                webbrowser.open(url)
                write_log("已尝试自动打开浏览器")
            except Exception as exc:
                write_log(f"自动打开浏览器失败：{exc}")

        threading.Timer(2.5, open_browser).start()
        atexit.register(lambda: write_log(f"{APP_NAME} 已退出"))

        sys.argv = [
            "streamlit",
            "run",
            str(app_path),
            "--server.address",
            "127.0.0.1",
            "--server.port",
            str(port),
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
            "--client.showSidebarNavigation",
            "false",
            "--global.developmentMode",
            "false",
        ]
        from streamlit.web.cli import main as streamlit_main

        streamlit_main()
    except Exception:
        error = traceback.format_exc()
        show_error(f"启动失败：\n{error}")
        raise


if __name__ == "__main__":
    main()
