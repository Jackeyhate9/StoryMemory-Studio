from __future__ import annotations

import sqlite3
from typing import Any

from app.db.database import dumps
from app.db.models import MemoryExtraction


def _text(value: Any, default: str = "") -> str:
    return default if value is None else str(value)


def upsert_extraction(
    conn: sqlite3.Connection, project_id: int, chapter_id: int, extraction: MemoryExtraction
) -> None:
    summary = extraction.summary or {}
    conn.execute(
        """
        INSERT INTO chapter_summaries
        (project_id, chapter_id, short_summary, detailed_summary, key_characters_json,
         key_locations_json, plot_threads_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(chapter_id) DO UPDATE SET
          short_summary=excluded.short_summary,
          detailed_summary=excluded.detailed_summary,
          key_characters_json=excluded.key_characters_json,
          key_locations_json=excluded.key_locations_json,
          plot_threads_json=excluded.plot_threads_json
        """,
        (
            project_id,
            chapter_id,
            _text(summary.get("short_summary")),
            _text(summary.get("detailed_summary")),
            dumps(summary.get("key_characters", [])),
            dumps(summary.get("key_locations", [])),
            dumps(summary.get("plot_threads", [])),
        ),
    )

    for character in extraction.characters:
        name = character.get("name")
        if not name:
            continue
        conn.execute(
            """
            INSERT INTO characters
            (project_id, name, aliases_json, role, appearance, personality, motivation,
             secrets, abilities, status, current_location, hard_constraints,
             first_chapter_id, last_seen_chapter_id, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name) DO UPDATE SET
              role=COALESCE(NULLIF(excluded.role,''), role),
              appearance=COALESCE(NULLIF(excluded.appearance,''), appearance),
              personality=COALESCE(NULLIF(excluded.personality,''), personality),
              motivation=COALESCE(NULLIF(excluded.motivation,''), motivation),
              abilities=COALESCE(NULLIF(excluded.abilities,''), abilities),
              status=COALESCE(NULLIF(excluded.status,''), status),
              current_location=COALESCE(NULLIF(excluded.current_location,''), current_location),
              hard_constraints=COALESCE(NULLIF(excluded.hard_constraints,''), hard_constraints),
              last_seen_chapter_id=excluded.last_seen_chapter_id,
              updated_at=CURRENT_TIMESTAMP
            """,
            (
                project_id,
                name,
                dumps(character.get("aliases", [])),
                _text(character.get("role")),
                _text(character.get("appearance")),
                _text(character.get("personality")),
                _text(character.get("motivation")),
                _text(character.get("secrets")),
                _text(character.get("abilities")),
                _text(character.get("status"), "active"),
                _text(character.get("current_location")),
                _text(character.get("hard_constraints")),
                chapter_id,
                chapter_id,
                dumps(character),
            ),
        )

    for rel in extraction.relationship_changes:
        conn.execute(
            """
            INSERT INTO character_relationships
            (project_id, character_a_name, character_b_name, relationship_type, status,
             description, evidence, chapter_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                _text(rel.get("character_a")),
                _text(rel.get("character_b")),
                _text(rel.get("relationship_type")),
                _text(rel.get("status")),
                _text(rel.get("description")),
                _text(rel.get("evidence")),
                chapter_id,
            ),
        )

    for loc in extraction.locations:
        if not loc.get("name"):
            continue
        conn.execute(
            """
            INSERT INTO locations
            (project_id, name, type, description, rules, connected_locations_json, first_chapter_id, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name) DO UPDATE SET
              description=COALESCE(NULLIF(excluded.description,''), description),
              rules=COALESCE(NULLIF(excluded.rules,''), rules)
            """,
            (
                project_id,
                _text(loc.get("name")),
                _text(loc.get("type")),
                _text(loc.get("description")),
                _text(loc.get("rules")),
                dumps(loc.get("connected_locations", [])),
                chapter_id,
                dumps(loc),
            ),
        )

    for org in extraction.organizations:
        if not org.get("name"):
            continue
        conn.execute(
            """
            INSERT INTO organizations
            (project_id, name, type, description, leader, allies_json, enemies_json, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name) DO UPDATE SET
              description=COALESCE(NULLIF(excluded.description,''), description),
              status=COALESCE(NULLIF(excluded.status,''), status)
            """,
            (
                project_id,
                _text(org.get("name")),
                _text(org.get("type")),
                _text(org.get("description")),
                _text(org.get("leader")),
                dumps(org.get("allies", [])),
                dumps(org.get("enemies", [])),
                _text(org.get("status")),
            ),
        )

    for item in extraction.items:
        if not item.get("name"):
            continue
        conn.execute(
            """
            INSERT INTO items
            (project_id, name, type, description, owner, location, status, constraints, first_chapter_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name) DO UPDATE SET
              owner=COALESCE(NULLIF(excluded.owner,''), owner),
              location=COALESCE(NULLIF(excluded.location,''), location),
              status=COALESCE(NULLIF(excluded.status,''), status)
            """,
            (
                project_id,
                _text(item.get("name")),
                _text(item.get("type")),
                _text(item.get("description")),
                _text(item.get("owner")),
                _text(item.get("location")),
                _text(item.get("status")),
                _text(item.get("constraints")),
                chapter_id,
            ),
        )

    for ability in extraction.abilities:
        if not ability.get("name"):
            continue
        conn.execute(
            """
            INSERT INTO abilities
            (project_id, name, owner, system, description, limitations, cost, level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name, owner) DO UPDATE SET
              description=COALESCE(NULLIF(excluded.description,''), description),
              limitations=COALESCE(NULLIF(excluded.limitations,''), limitations),
              level=COALESCE(NULLIF(excluded.level,''), level)
            """,
            (
                project_id,
                _text(ability.get("name")),
                _text(ability.get("owner")),
                _text(ability.get("system")),
                _text(ability.get("description")),
                _text(ability.get("limitations")),
                _text(ability.get("cost")),
                _text(ability.get("level")),
            ),
        )

    for rule in extraction.world_rules:
        if rule.get("rule_text"):
            conn.execute(
                "INSERT INTO world_rules (project_id, category, rule_text, rigidity, source, chapter_id) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    project_id,
                    _text(rule.get("category")),
                    _text(rule.get("rule_text")),
                    _text(rule.get("rigidity"), "hard"),
                    _text(rule.get("source")),
                    chapter_id,
                ),
            )

    conn.execute("DELETE FROM chapter_facts WHERE project_id = ? AND chapter_id = ?", (project_id, chapter_id))
    for fact in extraction.facts:
        fact_text = fact.get("fact_text") or fact.get("text")
        if not fact_text:
            continue
        conn.execute(
            """
            INSERT INTO chapter_facts
            (project_id, chapter_id, fact_type, subject, predicate, object, fact_text, certainty, source_quote)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                chapter_id,
                _text(fact.get("fact_type")),
                _text(fact.get("subject")),
                _text(fact.get("predicate")),
                _text(fact.get("object")),
                _text(fact_text),
                float(fact.get("certainty", 1.0) or 1.0),
                _text(fact.get("source_quote")),
            ),
        )

    for thread in extraction.plot_threads:
        if not thread.get("name"):
            continue
        conn.execute(
            """
            INSERT INTO plot_threads
            (project_id, name, thread_type, status, summary, related_characters_json, first_chapter_id, last_chapter_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name) DO UPDATE SET
              status=COALESCE(NULLIF(excluded.status,''), status),
              summary=COALESCE(NULLIF(excluded.summary,''), summary),
              last_chapter_id=excluded.last_chapter_id
            """,
            (
                project_id,
                _text(thread.get("name")),
                _text(thread.get("thread_type")),
                _text(thread.get("status"), "open"),
                _text(thread.get("summary")),
                dumps(thread.get("related_characters", [])),
                chapter_id,
                chapter_id,
            ),
        )

    for fs in extraction.foreshadows:
        if not fs.get("name"):
            continue
        conn.execute(
            """
            INSERT INTO foreshadows
            (project_id, name, first_chapter_id, related_characters_json, related_items_json,
             related_thread, status, expected_resolution_chapter, resolution_method,
             last_mentioned_chapter_id, risk_note, evidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, name) DO UPDATE SET
              status=COALESCE(NULLIF(excluded.status,''), status),
              resolution_method=COALESCE(NULLIF(excluded.resolution_method,''), resolution_method),
              last_mentioned_chapter_id=excluded.last_mentioned_chapter_id,
              risk_note=COALESCE(NULLIF(excluded.risk_note,''), risk_note)
            """,
            (
                project_id,
                _text(fs.get("name")),
                chapter_id,
                dumps(fs.get("related_characters", [])),
                dumps(fs.get("related_items", [])),
                _text(fs.get("related_thread")),
                _text(fs.get("status"), "unresolved"),
                fs.get("expected_resolution_chapter"),
                _text(fs.get("resolution_method")),
                chapter_id,
                _text(fs.get("risk_note")),
                _text(fs.get("evidence")),
            ),
        )

    for event in extraction.timeline_events:
        event_text = event.get("event_text") or event.get("text")
        if not event_text:
            continue
        conn.execute(
            """
            INSERT INTO timeline_events
            (project_id, chapter_id, story_time, sort_key, event_text, location, characters_json, duration, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                chapter_id,
                _text(event.get("story_time")),
                _text(event.get("sort_key")),
                _text(event_text),
                _text(event.get("location")),
                dumps(event.get("characters", [])),
                _text(event.get("duration")),
                float(event.get("confidence", 1.0) or 1.0),
            ),
        )

    for question in extraction.unresolved_questions:
        text = question.get("question")
        if text:
            conn.execute(
                """
                INSERT INTO unresolved_questions
                (project_id, question, related_thread, related_characters_json, first_chapter_id, status, priority, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    _text(text),
                    _text(question.get("related_thread")),
                    dumps(question.get("related_characters", [])),
                    chapter_id,
                    _text(question.get("status"), "open"),
                    _text(question.get("priority"), "medium"),
                    _text(question.get("notes")),
                ),
            )

    write_memory_chunks(conn, project_id, chapter_id, extraction)


def write_memory_chunks(conn: sqlite3.Connection, project_id: int, chapter_id: int, extraction: MemoryExtraction) -> None:
    row = conn.execute("SELECT chapter_number FROM chapters WHERE id = ?", (chapter_id,)).fetchone()
    chapter_number = row["chapter_number"] if row else chapter_id
    conn.execute(
        "DELETE FROM memory_chunks WHERE project_id = ? AND source_type = 'chapter' AND source_id = ?",
        (project_id, chapter_id),
    )
    summary = extraction.summary or {}
    if summary.get("detailed_summary"):
        conn.execute(
            """
            INSERT INTO memory_chunks
            (project_id, source_type, source_id, chunk_type, title, content, keywords_json, importance)
            VALUES (?, 'chapter', ?, 'summary', ?, ?, ?, ?)
            """,
            (
                project_id,
                chapter_id,
                f"Chapter {chapter_number} summary",
                _text(summary.get("detailed_summary")),
                dumps(summary.get("key_characters", []) + summary.get("key_locations", [])),
                75,
            ),
        )
    for fact in extraction.facts:
        text = fact.get("fact_text") or fact.get("text")
        if text:
            conn.execute(
                """
                INSERT INTO memory_chunks
                (project_id, source_type, source_id, chunk_type, title, content, keywords_json, importance)
                VALUES (?, 'chapter', ?, 'fact', ?, ?, ?, ?)
                """,
                (
                    project_id,
                    chapter_id,
                    _text(fact.get("subject"), "fact"),
                    _text(text),
                    dumps([fact.get("subject"), fact.get("object")]),
                    95,
                ),
            )
