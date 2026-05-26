from __future__ import annotations

import re
import sqlite3
from typing import Any

from app.db.database import loads, rows_to_dicts


def keywords(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[\w\u4e00-\u9fff]{2,}", text or "")}


def score_text(text: str, query_terms: set[str]) -> int:
    hay = (text or "").lower()
    return sum(1 for term in query_terms if term and term in hay)


def _is_context_worthy_fact(text: str) -> bool:
    if not text:
        return False
    if len(text) < 14 or len(text) > 180:
        return False
    if text.count("“") != text.count("”"):
        return False
    if len(re.findall(r"[A-Za-z]", text)) > 8:
        return False
    if text.startswith(("”", "，", "。", "、", "；", "：")):
        return False
    if text.endswith(("的", "了", "着", "过", "和", "与", "或", "但", "却", "把", "被")):
        return False
    weak_fragments = ("声音", "目光", "沉默", "空气", "脸色", "站着", "看着", "没说话")
    if len(text) < 35 and any(fragment in text for fragment in weak_fragments):
        return False
    useful_markers = (
        "发现",
        "留下",
        "取出",
        "交给",
        "收下",
        "答应",
        "拒绝",
        "承认",
        "写着",
        "刻着",
        "缺页",
        "残玉",
        "印章",
        "账本",
        "请帖",
        "罗公馆",
        "范允初",
        "叶含章",
        "改松岩",
    )
    return len(text) >= 45 or any(marker in text for marker in useful_markers)


class MemoryRetriever:
    def __init__(self, conn: sqlite3.Connection, project_id: int):
        self.conn = conn
        self.project_id = project_id

    def characters(self, names: list[str]) -> list[dict[str, Any]]:
        if not names:
            return []
        placeholders = ",".join("?" for _ in names)
        rows = self.conn.execute(
            f"SELECT * FROM characters WHERE project_id = ? AND name IN ({placeholders})",
            (self.project_id, *names),
        ).fetchall()
        return rows_to_dicts(rows)

    def locations(self, names: list[str]) -> list[dict[str, Any]]:
        if not names:
            return []
        placeholders = ",".join("?" for _ in names)
        rows = self.conn.execute(
            f"SELECT * FROM locations WHERE project_id = ? AND name IN ({placeholders})",
            (self.project_id, *names),
        ).fetchall()
        return rows_to_dicts(rows)

    def world_rules(self) -> list[dict[str, Any]]:
        return rows_to_dicts(
            self.conn.execute(
                "SELECT * FROM world_rules WHERE project_id = ? AND is_active = 1 ORDER BY rigidity DESC, id",
                (self.project_id,),
            ).fetchall()
        )

    def forbidden_rules(self) -> list[dict[str, Any]]:
        return rows_to_dicts(
            self.conn.execute(
                "SELECT * FROM forbidden_rules WHERE project_id = ? AND is_active = 1 ORDER BY severity DESC, id",
                (self.project_id,),
            ).fetchall()
        )

    def recent_chapters(self, before_number: int, limit: int = 5) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT c.*, s.short_summary, s.detailed_summary, s.key_characters_json, s.key_locations_json
            FROM chapters c
            LEFT JOIN chapter_summaries s ON s.chapter_id = c.id
            WHERE c.project_id = ? AND c.chapter_number < ?
            ORDER BY c.chapter_number DESC LIMIT ?
            """,
            (self.project_id, before_number, limit),
        ).fetchall()
        return rows_to_dicts(rows)

    def previous_chapter_bridge(self, before_number: int, tail_chars: int = 700) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT c.*, s.short_summary, s.detailed_summary
            FROM chapters c
            LEFT JOIN chapter_summaries s ON s.chapter_id = c.id
            WHERE c.project_id = ? AND c.chapter_number < ?
            ORDER BY c.chapter_number DESC LIMIT 1
            """,
            (self.project_id, before_number),
        ).fetchone()
        if not row:
            return None
        item = dict(row)
        content = item.get("content") or ""
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
        ending = "\n\n".join(paragraphs[-8:]) if paragraphs else content[-tail_chars:]
        if len(ending) > tail_chars:
            ending = ending[-tail_chars:]
        item["ending_excerpt"] = ending
        return item

    def facts_recent(self, before_number: int, limit_chapters: int = 3) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT f.*, c.chapter_number
            FROM chapter_facts f
            JOIN chapters c ON c.id = f.chapter_id
            WHERE f.project_id = ? AND c.chapter_number < ? AND f.is_active = 1
            ORDER BY c.chapter_number DESC, f.id DESC
            LIMIT ?
            """,
            (self.project_id, before_number, limit_chapters * 30),
        ).fetchall()
        facts = []
        for row in rows_to_dicts(rows):
            text = (row.get("fact_text") or "").strip()
            if not _is_context_worthy_fact(text):
                continue
            facts.append(row)
            if len(facts) >= limit_chapters * 8:
                break
        return facts

    def foreshadows(self, names: list[str] | None = None) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM foreshadows WHERE project_id = ? ORDER BY status, id", (self.project_id,)
        ).fetchall()
        items = rows_to_dicts(rows)
        if not names:
            return [x for x in items if x.get("status") in {"unresolved", "partial", "部分回收", "未回收"}]
        terms = set(names)
        return [x for x in items if x["name"] in terms or x.get("related_thread") in terms]

    def relationships(self, character_names: list[str]) -> list[dict[str, Any]]:
        if not character_names:
            return []
        placeholders = ",".join("?" for _ in character_names)
        rows = self.conn.execute(
            f"""
            SELECT * FROM character_relationships
            WHERE project_id = ? AND (character_a_name IN ({placeholders}) OR character_b_name IN ({placeholders}))
            ORDER BY updated_at DESC LIMIT 80
            """,
            (self.project_id, *character_names, *character_names),
        ).fetchall()
        return rows_to_dicts(rows)

    def timeline(self, query: str = "", limit: int = 80) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM timeline_events WHERE project_id = ? ORDER BY COALESCE(sort_key, ''), id LIMIT ?",
            (self.project_id, limit),
        ).fetchall()
        events = rows_to_dicts(rows)
        if not query:
            return events
        terms = keywords(query)
        return sorted(events, key=lambda e: score_text(str(e), terms), reverse=True)[:limit]

    def style_profile(self) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM style_profiles WHERE project_id = ? ORDER BY is_default DESC, id DESC LIMIT 1",
            (self.project_id,),
        ).fetchone()
        return dict(row) if row else None

    def chunks(self, query: str, limit: int = 80) -> list[dict[str, Any]]:
        terms = keywords(query)
        rows = self.conn.execute(
            "SELECT * FROM memory_chunks WHERE project_id = ? ORDER BY importance DESC, id DESC LIMIT 500",
            (self.project_id,),
        ).fetchall()
        chunks = rows_to_dicts(rows)
        for chunk in chunks:
            chunk["keywords"] = loads(chunk.get("keywords_json"), [])
            chunk["score"] = chunk.get("importance", 50) + score_text(chunk.get("content", ""), terms) * 15
        return sorted(chunks, key=lambda c: c["score"], reverse=True)[:limit]

    def archive_chunks(self, query: str, limit: int = 30) -> list[dict[str, Any]]:
        chunks = self.chunks(query, limit=limit * 3)
        archival_types = {"outline", "summary", "world", "style", "project"}
        return [chunk for chunk in chunks if chunk.get("chunk_type") in archival_types][:limit]
