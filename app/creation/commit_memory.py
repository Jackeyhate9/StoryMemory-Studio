from __future__ import annotations

import json
import sqlite3

from app.context.builder import ContextBuilder
from app.db.database import db_session, dumps, get_project, init_db, log_generation
from app.db.models import ContextRequest
from app.memory.extractor import heuristic_extract
from app.memory.writer import upsert_extraction
from app.schemas.create_novel import CreateNovelResult


def project_name_from_title(title: str) -> str:
    import re

    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", title).strip("_")
    return cleaned[:48] or "novel_project"


def _insert_initial_memory(conn: sqlite3.Connection, project_id: int, result: CreateNovelResult) -> int:
    for rule in result.world_rules:
        conn.execute(
            "INSERT INTO world_rules (project_id, category, rule_text, rigidity, source) VALUES (?, ?, ?, ?, ?)",
            (project_id, rule.category, rule.rule_text, rule.rigidity, rule.source),
        )

    for rule in result.forbidden_rules:
        conn.execute(
            "INSERT INTO forbidden_rules (project_id, rule_text, category, severity, source) VALUES (?, ?, ?, ?, ?)",
            (project_id, rule.rule_text, rule.category, rule.severity, rule.source),
        )

    for ch in result.characters:
        conn.execute(
            """
            INSERT INTO characters
            (project_id, name, aliases_json, role, appearance, personality, motivation, secrets,
             abilities, status, current_location, hard_constraints, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name) DO UPDATE SET
              role=excluded.role, personality=excluded.personality, motivation=excluded.motivation,
              status=excluded.status, hard_constraints=excluded.hard_constraints, updated_at=CURRENT_TIMESTAMP
            """,
            (
                project_id,
                ch.name,
                dumps(ch.aliases),
                ch.role,
                ch.appearance,
                ch.personality,
                ch.motivation,
                ch.secrets,
                ch.abilities,
                ch.status,
                ch.current_location,
                ch.hard_constraints,
                ch.model_dump_json(),
            ),
        )

    for rel in result.relationships:
        conn.execute(
            """
            INSERT INTO character_relationships
            (project_id, character_a_name, character_b_name, relationship_type, status, description, evidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, rel.character_a, rel.character_b, rel.relationship_type, rel.status, rel.description, rel.evidence),
        )

    for loc in result.locations:
        conn.execute(
            """
            INSERT INTO locations (project_id, name, type, description, rules, connected_locations_json, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name) DO UPDATE SET description=excluded.description, rules=excluded.rules
            """,
            (project_id, loc.name, loc.type, loc.description, loc.rules, dumps(loc.connected_locations), loc.model_dump_json()),
        )

    for org in result.organizations:
        conn.execute(
            """
            INSERT INTO organizations (project_id, name, type, description, leader, allies_json, enemies_json, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name) DO UPDATE SET description=excluded.description, status=excluded.status
            """,
            (project_id, org.name, org.type, org.description, org.leader, dumps(org.allies), dumps(org.enemies), org.status),
        )

    for item in result.items:
        conn.execute(
            """
            INSERT INTO items (project_id, name, type, description, owner, location, status, constraints)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name) DO UPDATE SET owner=excluded.owner, status=excluded.status
            """,
            (project_id, item.name, item.type, item.description, item.owner, item.location, item.status, item.constraints),
        )

    for ability in result.abilities:
        conn.execute(
            """
            INSERT INTO abilities (project_id, name, owner, system, description, limitations, cost, level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name, owner) DO UPDATE SET description=excluded.description, limitations=excluded.limitations
            """,
            (project_id, ability.name, ability.owner, ability.system, ability.description, ability.limitations, ability.cost, ability.level),
        )

    for thread in result.plot_threads:
        conn.execute(
            """
            INSERT INTO plot_threads
            (project_id, name, thread_type, status, summary, related_characters_json)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name) DO UPDATE SET status=excluded.status, summary=excluded.summary
            """,
            (project_id, thread.name, thread.thread_type, thread.status, thread.summary, dumps(thread.related_characters)),
        )

    for fs in result.foreshadows:
        conn.execute(
            """
            INSERT INTO foreshadows
            (project_id, name, related_characters_json, related_items_json, related_thread, status,
             expected_resolution_chapter, resolution_method, risk_note, evidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name) DO UPDATE SET status=excluded.status, risk_note=excluded.risk_note
            """,
            (
                project_id,
                fs.name,
                dumps(fs.related_characters),
                dumps(fs.related_items),
                fs.related_thread,
                fs.status,
                fs.expected_resolution_chapter,
                fs.resolution_method,
                fs.risk_note,
                fs.evidence,
            ),
        )

    for ev in result.timeline_events:
        conn.execute(
            """
            INSERT INTO timeline_events
            (project_id, story_time, sort_key, event_text, location, characters_json, duration, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, ev.story_time, ev.sort_key, ev.event_text, ev.location, dumps(ev.characters), ev.duration, ev.confidence),
        )

    style = result.style_profile
    conn.execute(
        """
        INSERT INTO style_profiles
        (project_id, name, platform, pov, sentence_length, dialogue_ratio, description_ratio,
         inner_monologue_ratio, high_point_density, common_patterns_json, banned_expressions_json,
         pacing, sample_text, profile_json, is_default)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(project_id, name) DO UPDATE SET profile_json=excluded.profile_json, is_default=1
        """,
        (
            project_id,
            style.name,
            style.platform,
            style.pov,
            style.sentence_length,
            style.dialogue_ratio,
            style.description_ratio,
            style.inner_monologue_ratio,
            style.high_point_density,
            dumps(style.common_patterns),
            dumps(style.banned_expressions),
            style.pacing,
            style.sample_text,
            dumps(style.profile),
        ),
    )

    for q in result.unresolved_questions:
        conn.execute(
            """
            INSERT INTO unresolved_questions
            (project_id, question, related_thread, related_characters_json, status, priority, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, q.question, q.related_thread, dumps(q.related_characters), q.status, q.priority, q.notes),
        )

    fc = result.first_chapter
    conn.execute(
        """
        INSERT INTO chapters (project_id, chapter_number, volume, title, content, outline, status, word_count)
        VALUES (?, 1, ?, ?, ?, ?, 'draft', ?)
        ON CONFLICT(project_id, chapter_number) DO UPDATE SET
          title=excluded.title, content=excluded.content, outline=excluded.outline,
          word_count=excluded.word_count, updated_at=CURRENT_TIMESTAMP
        """,
        (
            project_id,
            "第一卷",
            fc.title,
            fc.content,
            json.dumps([x.model_dump() for x in result.chapter_outlines], ensure_ascii=False, indent=2),
            len(fc.content),
        ),
    )
    chapter_id = conn.execute("SELECT id FROM chapters WHERE project_id = ? AND chapter_number = 1", (project_id,)).fetchone()["id"]
    extraction = heuristic_extract(fc.title, fc.content)
    extraction.summary["short_summary"] = fc.summary or extraction.summary.get("short_summary", "")
    extraction.facts = [{"fact_text": fact, "fact_type": "initial_fact"} for fact in fc.facts] or extraction.facts
    upsert_extraction(conn, project_id, chapter_id, extraction)
    return chapter_id


def commit_create_novel_result(result: CreateNovelResult, output_project: str | None = None, provider: str = "none") -> dict:
    init_db()
    project_name = output_project or project_name_from_title(result.project.title)
    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO projects (name, title, description, genre, target_platform, current_volume, metadata_json)
            VALUES (?, ?, ?, ?, ?, '第一卷', ?)
            ON CONFLICT(name) DO UPDATE SET
              title=excluded.title, description=excluded.description, genre=excluded.genre,
              target_platform=excluded.target_platform, metadata_json=excluded.metadata_json,
              updated_at=CURRENT_TIMESTAMP
            """,
            (
                project_name,
                result.project.title,
                result.project.logline,
                result.project.genre,
                result.project.platform,
                dumps(
                    {
                        "expected_chapters": result.project.expected_chapters,
                        "chapter_word_count": result.project.chapter_word_count,
                        "core_selling_points": result.project.core_selling_points,
                        "volume_outline": result.volume_outline,
                    }
                ),
            ),
        )
        project = get_project(conn, project_name)
        chapter_id = _insert_initial_memory(conn, project["id"], result)
        log_generation(
            conn,
            project["id"],
            "create_novel_commit",
            provider=provider,
            response=result.model_dump_json(),
            structured=result.model_dump(),
            chapter_id=chapter_id,
        )
        context = ContextBuilder(conn, project).build(
            ContextRequest(
                project=project_name,
                chapter_number=2,
                chapter_goal=result.chapter_outlines[1].chapter_goal if len(result.chapter_outlines) > 1 else "承接第一章继续推进主线",
                chapter_outline=json.dumps(result.chapter_outlines[1].model_dump(), ensure_ascii=False) if len(result.chapter_outlines) > 1 else "",
                characters=[c.name for c in result.characters[:3]],
                locations=[l.name for l in result.locations[:2]],
                mode="standard",
            )
        )
    return {"project": project_name, "chapter_id": chapter_id, "second_chapter_context": context}

