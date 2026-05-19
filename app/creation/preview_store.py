from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from app.schemas.create_novel import CreateNovelResult

PREVIEW_DIR = Path(__file__).parents[2] / "data" / "previews"


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", text).strip("_")
    return cleaned[:40] or "novel"


def save_preview(result: CreateNovelResult, name: str | None = None) -> Path:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{slugify(name or result.project.title)}.json"
    path = PREVIEW_DIR / filename
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_preview(path: str | Path) -> CreateNovelResult:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return CreateNovelResult.model_validate(data)


def save_preview_text(text: str, name: str) -> Path:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = PREVIEW_DIR / f"{timestamp}_{slugify(name)}_edited.json"
    result = CreateNovelResult.model_validate(json.loads(text))
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return path

