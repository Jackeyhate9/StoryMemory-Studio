from __future__ import annotations

import re
from pathlib import Path

from app.db.models import MemoryExtraction
from app.llm.client import LLMClient, extract_json, repair_json_with_llm


PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "extract_memory.md"


def heuristic_extract(title: str, content: str) -> MemoryExtraction:
    candidates = re.findall(r"[A-Z][a-zA-Z]{1,20}|[\u4e00-\u9fff]{2,4}", content[:4000])
    stop = {
        "玫瑰", "大厦", "资本", "热搜", "手机", "电梯", "灯光", "玻璃", "宴会", "会议", "项目", "消息",
        "时候", "声音", "目光", "空气", "沉默", "所有", "一个", "没有", "只是", "自己", "什么", "这里",
    }
    known_name_pattern = re.compile(r"^[谢林薛王许顾陆沈周陈宋赵何苏傅白][\u4e00-\u9fff]{1,2}$")
    bad_fragments = {"小姐", "以前", "负责", "是谁", "这里", "那里"}
    bad_suffixes = set("的一是在有和也就很不去过回冷合展说坐停低僵关自总")
    names = []
    for name in candidates:
        if name in stop:
            continue
        if any(fragment in name for fragment in bad_fragments):
            continue
        if len(name) > 3 or name[-1] in bad_suffixes:
            continue
        if re.match(r"^[A-Z]", name) or known_name_pattern.match(name):
            names.append(name)
    names = sorted(set(names))[:10]
    sentences = re.split(r"[。！？\n]+", content)
    facts = [{"fact_text": s.strip(), "fact_type": "chapter_fact"} for s in sentences if 4 <= len(s.strip()) <= 120][:20]
    summary_text = "；".join([s.strip() for s in sentences if s.strip()][:5])
    return MemoryExtraction(
        summary={
            "short_summary": summary_text[:300] or title,
            "detailed_summary": summary_text[:1200] or content[:1200],
            "key_characters": names[:6],
            "key_locations": [],
            "plot_threads": [],
        },
        characters=[{"name": n, "last_seen_note": "heuristic candidate"} for n in names[:6]],
        facts=facts,
        timeline_events=[{"event_text": facts[0]["fact_text"]}] if facts else [],
    )


class MemoryExtractor:
    def __init__(self, client: LLMClient | None = None):
        self.client = client

    def extract(self, title: str, content: str) -> MemoryExtraction:
        if self.client is None:
            return heuristic_extract(title, content)
        template = PROMPT_PATH.read_text(encoding="utf-8")
        prompt = template.format(chapter_title=title, chapter_content=content)
        raw = self.client.complete(prompt, temperature=0.1)
        try:
            data = extract_json(raw)
        except Exception:
            data = repair_json_with_llm(raw, self.client)
        return MemoryExtraction.model_validate(data)
