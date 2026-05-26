from __future__ import annotations

import json
import sqlite3
from typing import Any

from app.context.ranking import BASE_WEIGHTS, TOKEN_BUDGETS, fit_sections
from app.context.templates import CONTEXT_TEMPLATE
from app.db.models import ContextRequest
from app.memory.retriever import MemoryRetriever
from app.quality.ai_tone_feedback import feedback_block


def _bullets(rows: list[dict[str, Any]], fields: list[str]) -> str:
    lines = []
    for row in rows:
        parts = [str(row.get(field, "")).strip() for field in fields if row.get(field)]
        if parts:
            lines.append("- " + " | ".join(parts))
    return "\n".join(lines) or "- 暂无"


def _json_block(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) if value else "暂无"


def _style_block(style: dict[str, Any] | None) -> str:
    if not style:
        return "暂无"
    if style.get("safe_style_summary"):
        lines = [
            f"- 叙事视角：{style.get('pov') or style.get('narrative_pov') or '未指定'}",
            f"- 句式节奏：{style.get('sentence_profile_json') or style.get('sentence_length') or '未指定'}",
            f"- 段落风格：{style.get('paragraph_profile_json') or '未指定'}",
            f"- 对话比例：{style.get('dialogue_profile_json') or style.get('dialogue_ratio') or '未指定'}",
            f"- 情绪表达：{style.get('emotion_profile_json') or '未指定'}",
            f"- 悬念方式：{style.get('hook_profile_json') or '未指定'}",
            f"- 安全文风摘要：{style.get('safe_style_summary')}",
            f"- 应该遵守：{style.get('do_rules_json') or '[]'}",
            f"- 必须避免：{style.get('dont_rules_json') or '[]'}",
            "- 文风安全要求：只学习抽象风格，不复制原文表达；不复用样章句子、段落结构、独特比喻、专有设定；生成新的原创内容。",
        ]
        return "\n".join(lines)
    safe = dict(style)
    safe.pop("sample_text", None)
    return _json_block(safe)


def _previous_bridge_block(row: dict[str, Any] | None) -> str:
    if not row:
        return "- 暂无上一章。本章可以按大纲开局，但仍需快速进入具体场景。"
    summary = row.get("short_summary") or row.get("detailed_summary") or "暂无摘要"
    ending = row.get("ending_excerpt") or "暂无结尾摘录"
    return "\n".join(
        [
            f"- 上一章：第 {row.get('chapter_number')} 章《{row.get('title') or '未命名'}》",
            f"- 上一章摘要：{summary}",
            f"- 上一章结尾原文：\n{ending}",
            "- 本章承接要求：开头 300 字内必须回应上一章结尾中的具体物件、动作、声响、来客、消息或未完成对话。",
            "- 禁止承接方式：不要重新开局，不要只用“与此同时”“几天后”“风波未平”等空泛过渡。",
        ]
    )


class ContextBuilder:
    def __init__(self, conn: sqlite3.Connection, project: dict[str, Any]):
        self.conn = conn
        self.project = project
        self.retriever = MemoryRetriever(conn, project["id"])

    def build(self, request: ContextRequest) -> str:
        query = " ".join(
            [request.chapter_goal, request.chapter_outline, *request.characters, *request.locations, *request.plot_threads]
        )
        characters = self.retriever.characters(request.characters)
        locations = self.retriever.locations(request.locations)
        relationships = self.retriever.relationships(request.characters)
        previous_bridge = self.retriever.previous_chapter_bridge(request.chapter_number)
        recent = self.retriever.recent_chapters(request.chapter_number, 5)
        facts = self.retriever.facts_recent(request.chapter_number, 3)
        world_rules = self.retriever.world_rules()
        forbidden = self.retriever.forbidden_rules()
        foreshadows = self.retriever.foreshadows(request.foreshadows or request.plot_threads)
        timeline = self.retriever.timeline(query, 60)
        style = self.retriever.style_profile()
        chunks = self.retriever.archive_chunks(query, 30)

        sections = [
            (
                "hard_rules",
                BASE_WEIGHTS["world_rule"],
                _bullets(world_rules, ["category", "rule_text", "rigidity"]),
            ),
            (
                "forbidden",
                BASE_WEIGHTS["forbidden_rule"],
                _bullets(forbidden, ["severity", "category", "rule_text"]),
            ),
            (
                "characters",
                BASE_WEIGHTS["current_character"],
                _bullets(
                    characters,
                    [
                        "name",
                        "role",
                        "personality",
                        "motivation",
                        "abilities",
                        "status",
                        "current_location",
                        "hard_constraints",
                    ],
                ),
            ),
            (
                "relationships",
                BASE_WEIGHTS["previous_character"],
                _bullets(relationships, ["character_a_name", "character_b_name", "relationship_type", "status", "description"]),
            ),
            (
                "places_items",
                BASE_WEIGHTS["current_location"],
                _bullets(locations, ["name", "type", "description", "rules"]),
            ),
            (
                "foreshadows",
                BASE_WEIGHTS["unresolved_foreshadow"],
                _bullets(
                    foreshadows,
                    [
                        "name",
                        "status",
                        "related_thread",
                        "expected_resolution_chapter",
                        "resolution_method",
                        "risk_note",
                    ],
                ),
            ),
            ("previous_bridge", BASE_WEIGHTS["recent_fact"], _previous_bridge_block(previous_bridge)),
            (
                "recent_summaries",
                BASE_WEIGHTS["recent_fact"],
                _bullets(recent, ["chapter_number", "title", "detailed_summary", "short_summary"]),
            ),
            ("facts", BASE_WEIGHTS["recent_fact"], _bullets(facts, ["chapter_number", "fact_type", "fact_text"])),
            ("volume_progress", BASE_WEIGHTS["current_volume"], _bullets(timeline, ["story_time", "event_text", "location"])),
            ("style", BASE_WEIGHTS["style_profile"], _style_block(dict(style) if style else None)),
            (
                "archive",
                BASE_WEIGHTS["early_summary"],
                _bullets(chunks, ["chunk_type", "title", "content"]),
            ),
        ]
        budget = TOKEN_BUDGETS[request.mode]
        selected = {title: content for title, _, content in fit_sections(sections, budget)}

        return CONTEXT_TEMPLATE.format(
            task_goal="生成或审校长篇小说章节，优先保证设定、人物关系、伏笔、时间线、上一章承接和文风一致。",
            chapter_goal=request.chapter_goal or "未指定",
            chapter_outline=request.chapter_outline or "未指定",
            hard_rules=selected.get("hard_rules", "暂无"),
            characters=selected.get("characters", "暂无"),
            relationships=selected.get("relationships", "暂无"),
            places_items="\n".join([selected.get("places_items", "暂无"), selected.get("archive", "")]).strip(),
            foreshadows=selected.get("foreshadows", "暂无"),
            previous_chapter_bridge=selected.get("previous_bridge", "暂无上一章。"),
            recent_summaries=selected.get("recent_summaries", "暂无"),
            facts=selected.get("facts", "暂无"),
            volume_progress=selected.get("volume_progress", "暂无"),
            style=selected.get("style", "暂无"),
            ai_tone_feedback=feedback_block(self.conn, self.project["id"]),
            forbidden=selected.get("forbidden", "暂无"),
            output_format="按用户指定模式输出；如生成正文，仅输出正文；如检查一致性，输出 JSON。",
        )
