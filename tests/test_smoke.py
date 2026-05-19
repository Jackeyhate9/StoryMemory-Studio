from app.memory.extractor import heuristic_extract


def test_heuristic_extract_summary():
    result = heuristic_extract("第一章", "林舟来到青岚城。他发现玉佩发烫。")
    assert result.summary["short_summary"]
    assert result.facts

