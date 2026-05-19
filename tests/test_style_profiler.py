from pathlib import Path

from app.db.database import db_session, get_project, init_db
from app.style.profiler import analyze_style
from app.style.similarity_guard import check_similarity
from app.style.style_schema import StyleProfileInput, StyleProfileResult
from app.style.style_store import default_style_profile, get_style_samples, save_style_profile


def test_style_profile_save_without_source(tmp_path, monkeypatch):
    db_path = tmp_path / "style.sqlite3"
    monkeypatch.setenv("STORYMEMORY_DB_PATH", str(db_path))
    from app.config import get_settings

    get_settings.cache_clear()
    init_db(db_path)
    with db_session(db_path) as conn:
        conn.execute("INSERT INTO projects (name, title) VALUES ('style_demo', '风格测试')")
    sample = "门外的雨忽然停了。她没有回头，只把那封信压进抽屉。"
    input_data = StyleProfileInput(style_name="克制悬疑", samples=[sample], target_usage=["小说正文"])
    profile = analyze_style(input_data, provider="none")
    assert isinstance(profile, StyleProfileResult)
    style_id = save_style_profile("style_demo", profile, [sample], save_source=False, set_default=True)
    samples = get_style_samples(style_id)
    assert samples[0]["sample_text"] is None
    assert samples[0]["sample_excerpt_safe"]
    default = default_style_profile("style_demo")
    assert default and default["id"] == style_id


def test_similarity_guard_detects_repeated_sentence():
    sample = "门外的雨忽然停了。她没有回头，只把那封信压进抽屉。走廊尽头传来脚步声。"
    generated = "门外的雨忽然停了。她没有回头，只把那封信压进抽屉。"
    report = check_similarity(sample, generated)
    assert report.risk_level in {"medium", "high"}
    assert report.matched_phrases

