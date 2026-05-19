def risk_level(foreshadow: dict, current_chapter: int) -> str:
    expected = foreshadow.get("expected_resolution_chapter")
    status = foreshadow.get("status")
    if status in {"resolved", "已回收"}:
        return "ok"
    if expected and current_chapter > int(expected):
        return "high"
    if expected and current_chapter >= int(expected) - 2:
        return "medium"
    return "low"

