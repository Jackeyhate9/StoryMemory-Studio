from app.creation.commit_memory import commit_create_novel_result
from app.creation.novel_builder import heuristic_create_novel
from app.creation.seed_parser import parse_seed
from app.schemas.create_novel import CreateNovelResult


def test_create_novel_schema_and_commit(tmp_path, monkeypatch):
    db_path = tmp_path / "storymemory.sqlite3"
    monkeypatch.setenv("STORYMEMORY_DB_PATH", str(db_path))
    from app.config import get_settings

    get_settings.cache_clear()
    seed = parse_seed(
        title="死后三日前",
        genre="都市悬疑时间循环",
        platform="番茄小说",
        premise="男主每死一次都会回到三天前",
        protagonist="陆沉，27岁，前刑警",
        goal="查清真相",
        selling_points="反转,推理",
        avoid="不要系统",
    )
    result = heuristic_create_novel(seed)
    assert isinstance(result, CreateNovelResult)
    assert result.chapter_outlines
    committed = commit_create_novel_result(result, output_project="test_zero_create", provider="none")
    assert committed["project"] == "test_zero_create"
    assert "【任务目标】" in committed["second_chapter_context"]

