import sqlite3

from app.creative_center import (
    adapt_chapter_for_ip,
    analyze_character_arc_for_project,
    analyze_pacing_for_chapter,
    analyze_platform_fit_for_chapter,
    detect_ai_tone_for_chapter,
    recommend_payoff_for_project,
)
from app.db.database import db_session, init_db
from app.platforms.platform_profiles import get_platform_profile
from app.quality.ai_tone_detector import detect_ai_tone


def seed_db(db_path):
    init_db(db_path)
    with db_session(db_path) as conn:
        cur = conn.execute("INSERT INTO projects (name, title) VALUES ('p', '测试项目')")
        project_id = cur.lastrowid
        ch = conn.execute(
            """
            INSERT INTO chapters (project_id, chapter_number, title, content, word_count)
            VALUES (?, 1, '第一章', ?, ?)
            """,
            (
                project_id,
                "他知道，这一切才刚刚开始。空气仿佛凝固了。\n门外忽然传来脚步声，他握紧玉佩。",
                50,
            ),
        )
        chapter_id = ch.lastrowid
        char = conn.execute(
            "INSERT INTO characters (project_id, name, role, motivation, status, importance) VALUES (?, '陆沉', '主角', '查清真相', '克制', 100)",
            (project_id,),
        )
        character_id = char.lastrowid
        conn.execute(
            "INSERT INTO foreshadows (project_id, name, status, first_chapter_id, last_mentioned_chapter_id, related_characters_json) VALUES (?, '黑玉佩发烫', 'unresolved', ?, ?, '[\"陆沉\"]')",
            (project_id, chapter_id, chapter_id),
        )
        return project_id, chapter_id, character_id


def test_ai_tone_detector_structured():
    report = detect_ai_tone("他知道，这一切才刚刚开始。命运的齿轮开始转动。")
    assert report.risk_level in {"medium", "high"}
    assert report.issues


def test_creative_center_modules_write_logs(tmp_path, monkeypatch):
    db_path = tmp_path / "creative.sqlite3"
    monkeypatch.setenv("STORYMEMORY_DB_PATH", str(db_path))
    from app.config import get_settings

    get_settings.cache_clear()
    project_id, chapter_id, character_id = seed_db(db_path)
    assert detect_ai_tone_for_chapter(project_id, chapter_id)["issues"]
    assert "chapter_score" in analyze_pacing_for_chapter(project_id, chapter_id)
    assert recommend_payoff_for_project(project_id)["recommendations"]
    assert analyze_character_arc_for_project(project_id, character_id)["character_name"] == "陆沉"
    assert analyze_platform_fit_for_chapter(project_id, chapter_id, "番茄小说")["platform"] == "番茄小说"
    adaptation = adapt_chapter_for_ip(project_id, chapter_id, "all")
    assert "comic_storyboard" in adaptation["json"]["adaptations"]
    assert "short_drama_script" in adaptation["json"]["adaptations"]
    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("SELECT COUNT(*) FROM generation_logs").fetchone()[0] >= 6
    finally:
        conn.close()


def test_builtin_platform_profile():
    profile = get_platform_profile("短剧")
    assert "冲突" in profile.chapter_opening
