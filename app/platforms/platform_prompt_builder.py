from __future__ import annotations

from app.platforms.platform_profiles import get_platform_profile


def platform_context_block(platform: str) -> str:
    profile = get_platform_profile(platform)
    return (
        "【平台适配规则】\n"
        f"- 平台：{profile.platform_name}\n"
        f"- 开头：{profile.chapter_opening}\n"
        f"- 节奏：{profile.pacing}\n"
        f"- 对白：{profile.dialogue}\n"
        f"- 描写：{profile.description}\n"
        f"- 结尾：{profile.ending_hook}\n"
        f"- 避免：{'、'.join(profile.avoid)}\n"
    )
