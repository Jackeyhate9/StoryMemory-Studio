TOKEN_BUDGETS = {
    "lite": 32_000,
    "standard": 128_000,
    "deepseek_long": 800_000,
    "full_audit": 1_000_000,
}

BASE_WEIGHTS = {
    "current_character": 100,
    "previous_character": 90,
    "current_location": 85,
    "unresolved_foreshadow": 85,
    "target_plot_thread": 80,
    "world_rule": 100,
    "forbidden_rule": 100,
    "recent_fact": 95,
    "current_volume": 75,
    "early_summary": 40,
    "style_profile": 70,
}


def estimate_tokens(text: str) -> int:
    # Chinese prose has fewer spaces, so use a conservative char-based estimate.
    return max(1, len(text) // 2)


def fit_sections(sections: list[tuple[str, int, str]], budget: int) -> list[tuple[str, int, str]]:
    used = 0
    selected: list[tuple[str, int, str]] = []
    for title, weight, content in sorted(sections, key=lambda x: x[1], reverse=True):
        tokens = estimate_tokens(content)
        if used + tokens <= budget or weight >= 100:
            selected.append((title, weight, content))
            used += tokens
    return selected

