from __future__ import annotations

import json
from pathlib import Path

from app.creation.commit_memory import commit_create_novel_result
from app.creation.novel_builder import build_novel_from_seed, regenerate_section
from app.creation.preview_store import load_preview, save_preview, save_preview_text
from app.creation.seed_parser import parse_seed
from app.schemas.create_novel import CreateNovelResult, NovelSeedInput


def create_preview(seed: NovelSeedInput, provider: str = "none") -> dict:
    result = build_novel_from_seed(seed, provider)
    path = save_preview(result, seed.title)
    return {"preview_path": str(path), "result": result}


def create_preview_from_kwargs(provider: str = "none", **kwargs) -> dict:
    seed = parse_seed(**kwargs)
    return create_preview(seed, provider)


def commit_preview(preview_path: str | Path, output_project: str | None = None, provider: str = "none") -> dict:
    result = load_preview(preview_path)
    return commit_create_novel_result(result, output_project, provider)


def commit_preview_text(preview_text: str, output_project: str | None = None, provider: str = "none") -> dict:
    result = CreateNovelResult.model_validate(json.loads(preview_text))
    path = save_preview(result, result.project.title)
    committed = commit_create_novel_result(result, output_project, provider)
    committed["preview_path"] = str(path)
    return committed


def regenerate_preview_section(seed: NovelSeedInput, preview_path: str | Path, section: str, provider: str = "none") -> dict:
    current = load_preview(preview_path)
    result = regenerate_section(seed, current, section, provider)
    path = save_preview(result, f"{result.project.title}_{section}")
    return {"preview_path": str(path), "result": result}
