from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def data_sep() -> str:
    return ";" if sys.platform.startswith("win") else ":"


def clean_dir(path: Path) -> None:
    root = ROOT.resolve()
    target = path.resolve()
    if target == root or root not in target.parents:
        raise RuntimeError(f"拒绝清理工作区之外的目录：{target}")
    if target.exists():
        shutil.rmtree(target)


def pyinstaller_path() -> Path:
    candidates = [
        ROOT / ".venv" / "Scripts" / "pyinstaller.exe",
        Path(sys.executable).with_name("pyinstaller.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise SystemExit("未找到 PyInstaller。请先运行：pip install -r requirements.txt")


def copy_tree_clean(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    if src.exists():
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))
    else:
        dst.mkdir(parents=True, exist_ok=True)


def build() -> None:
    clean_dir(ROOT / "build")
    clean_dir(ROOT / "dist")

    sep = data_sep()
    data_args = [
        f"{ROOT / 'app'}{sep}app",
        f"{ROOT / '.streamlit'}{sep}.streamlit",
        f"{ROOT / '.env.example'}{sep}.",
        f"{ROOT / 'README.md'}{sep}.",
    ]

    hidden_imports = [
        "watchdog.observers.winapi",
        "streamlit.web.cli",
        "app.db.database",
        "app.ui.services",
        "app.ui.layout",
        "app.ui.navigation",
        "app.ui.sections.creation.create_novel_wizard",
        "app.ui.sections.creation.project_manager",
        "app.ui.sections.creation.import_chapter",
        "app.ui.sections.memory.memory_dashboard",
        "app.ui.sections.memory.memory_editor",
        "app.ui.sections.memory.backup_restore",
        "app.ui.sections.writing.generate_chapter",
        "app.ui.sections.writing.edit_export_chapter",
        "app.ui.sections.writing.style_profiler",
        "app.ui.sections.writing.model_settings",
        "app.ui.sections.consistency.consistency_checker",
        "app.ui.sections.consistency.foreshadow_manager",
        "app.ui.sections.consistency.timeline_manager",
        "app.ui.sections.consistency.character_arc_tracker",
        "app.ui.sections.optimization.ai_tone_detector",
        "app.ui.sections.optimization.pacing_analyzer",
        "app.ui.sections.optimization.foreshadow_payoff",
        "app.ui.sections.optimization.platform_adapter",
        "app.ui.sections.adaptation.adaptation_matrix",
        "app.ui.sections.adaptation.comic_storyboard",
        "app.ui.sections.adaptation.short_drama_script",
        "app.ui.sections.adaptation.xiaohongshu_post",
        "app.ui.sections.adaptation.poster_prompt",
    ]

    cmd = [
        str(pyinstaller_path()),
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "StoryMemoryStudio",
        "--collect-all",
        "streamlit",
        "--collect-all",
        "altair",
        "--collect-all",
        "plotly",
        "--collect-data",
        "docx",
    ]
    for item in hidden_imports:
        cmd.extend(["--hidden-import", item])
    for item in data_args:
        cmd.extend(["--add-data", item])
    cmd.append(str(ROOT / "launcher.py"))

    subprocess.run(cmd, cwd=ROOT, check=True)

    dist = ROOT / "dist"
    (dist / "data").mkdir(parents=True, exist_ok=True)
    (dist / "exports").mkdir(parents=True, exist_ok=True)
    (dist / "logs").mkdir(parents=True, exist_ok=True)
    (dist / "start_log.txt").write_text("", encoding="utf-8")
    shutil.copy2(ROOT / ".env.example", dist / ".env.example")
    if (ROOT / "README.md").exists():
        shutil.copy2(ROOT / "README.md", dist / "README.md")
        shutil.copy2(ROOT / "README.md", dist / "README_使用说明.md")
    copy_tree_clean(ROOT / "app" / "prompts", dist / "prompts")
    shutil.copy2(ROOT / "app" / "db" / "schema.sql", dist / "schema.sql")

    exe = dist / "StoryMemoryStudio.exe"
    if not exe.exists():
        raise RuntimeError("打包结束但没有找到 dist/StoryMemoryStudio.exe")
    print(f"打包完成：{exe}")
    print("下一步可运行：dist\\StoryMemoryStudio.exe")


if __name__ == "__main__":
    build()
