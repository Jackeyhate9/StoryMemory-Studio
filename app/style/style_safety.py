from __future__ import annotations

import hashlib
import re
from pathlib import Path

from docx import Document


def clean_sample_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def safe_excerpt(text: str, limit: int = 600) -> str:
    cleaned = clean_sample_text(text)
    return cleaned[:limit]


def text_hash(text: str) -> str:
    return hashlib.sha256(clean_sample_text(text).encode("utf-8")).hexdigest()


def read_style_file(path: str | Path) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in {".txt", ".md"}:
        return p.read_text(encoding="utf-8-sig")
    if suffix == ".docx":
        doc = Document(p)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())
    if suffix == ".doc":
        # Legacy .doc is often binary. This fallback supports HTML/text .doc files.
        return p.read_bytes().decode("utf-8", errors="ignore")
    raise ValueError(f"Unsupported style sample format: {suffix}")


def sample_stats(text: str) -> dict:
    cleaned = clean_sample_text(text)
    paragraphs = [p for p in cleaned.split("\n") if p.strip()]
    sentences = re.split(r"[。！？!?]+", cleaned)
    sentences = [s for s in sentences if s.strip()]
    dialogue_marks = cleaned.count("“") + cleaned.count('"')
    return {
        "chars": len(cleaned),
        "paragraphs": len(paragraphs),
        "sentences": len(sentences),
        "avg_sentence_chars": round(sum(len(s) for s in sentences) / max(1, len(sentences)), 1),
        "avg_paragraph_chars": round(sum(len(p) for p in paragraphs) / max(1, len(paragraphs)), 1),
        "dialogue_mark_count": dialogue_marks,
    }

