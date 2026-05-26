from __future__ import annotations

import re
from pathlib import Path

from app.db.models import MemoryExtraction
from app.llm.client import LLMClient, extract_json, repair_json_with_llm


PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "extract_memory.md"


def _clean_sentence(sentence: str) -> str:
    return re.sub(r"\s+", " ", sentence).strip(" \t\r\n，。；：、")


def _is_fact_sentence(sentence: str) -> bool:
    text = _clean_sentence(sentence)
    if len(text) < 6 or len(text) > 180:
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
        "拒绝",
        "答应",
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


def heuristic_extract(title: str, content: str) -> MemoryExtraction:
    candidates = re.findall(r"[A-Z][a-zA-Z]{1,20}|[\u4e00-\u9fff]{2,4}", content[:4000])
    stop = {
        "大门",
        "柜台",
        "账本",
        "残玉",
        "请帖",
        "声音",
        "目光",
        "空气",
        "沉默",
        "所有",
        "一个",
        "没有",
        "只是",
        "自己",
        "什么",
        "这里",
        "那里",
    }
    known_name_pattern = re.compile(r"^[改叶范罗宫周沈林王谢陆陈宋赵何苏傅白][\u4e00-\u9fff]{1,2}$")
    bad_fragments = {"小姐", "以前", "负责", "是谁", "这里", "那里"}
    bad_suffixes = set("的一是在有和也就很不去过回说坐停低关自")
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

    sentences = [_clean_sentence(s) for s in re.split(r"[。！？!?；;\n]+", content)]
    useful_sentences = [s for s in sentences if len(s) >= 12]
    facts = [{"fact_text": s, "fact_type": "chapter_fact"} for s in sentences if _is_fact_sentence(s)][:12]
    summary_text = "；".join(useful_sentences[:5])
    timeline = [{"event_text": facts[0]["fact_text"]}] if facts else []
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
        timeline_events=timeline,
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
