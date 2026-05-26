from app.memory.extractor import heuristic_extract


def test_heuristic_extract_keeps_context_worthy_facts_only():
    text = """改松岩看着柜台，没有说话。
空气安静下来。
叶含章取出半枚印章，放在残玉旁边。
改松岩发现账本最后一页缺页，纸边还残留淡淡银粉。
"""
    result = heuristic_extract("测试章", text)
    facts = [item["fact_text"] for item in result.facts]
    assert "叶含章取出半枚印章，放在残玉旁边" in facts
    assert "改松岩发现账本最后一页缺页，纸边还残留淡淡银粉" in facts
    assert all("空气安静" not in fact for fact in facts)
