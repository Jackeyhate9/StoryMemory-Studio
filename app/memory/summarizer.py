from app.memory.extractor import heuristic_extract


def summarize_chapter(title: str, content: str) -> dict:
    return heuristic_extract(title, content).summary

