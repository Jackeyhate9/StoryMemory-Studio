from __future__ import annotations


NAVIGATION = {
    "创作启动": {
        "icon": "Start",
        "description": "创建项目、导入章节、从零搭建小说。",
        "pages": {
            "从 0 创建小说": "creation.create_novel_wizard",
            "项目管理": "creation.project_manager",
            "章节导入": "creation.import_chapter",
        },
    },
    "记忆中枢": {
        "icon": "Memory",
        "description": "管理人物、伏笔、世界观、章节事实等长期记忆。",
        "pages": {
            "记忆库看板": "memory.memory_dashboard",
            "记忆编辑器": "memory.memory_editor",
            "备份与恢复": "memory.backup_restore",
        },
    },
    "章节创作": {
        "icon": "Write",
        "description": "生成、编辑、导出章节，并管理文风和模型。",
        "pages": {
            "章节生成": "writing.generate_chapter",
            "章节编辑与导出": "writing.edit_export_chapter",
            "文风学习器": "writing.style_profiler",
            "模型与数据设置": "writing.model_settings",
        },
    },
    "一致性管理": {
        "icon": "Check",
        "description": "检查设定、时间线、伏笔、人物弧光是否一致。",
        "pages": {
            "一致性检查": "consistency.consistency_checker",
            "伏笔管理": "consistency.foreshadow_manager",
            "时间线管理": "consistency.timeline_manager",
            "人物弧光追踪": "consistency.character_arc_tracker",
        },
    },
    "质量优化": {
        "icon": "Tune",
        "description": "提升章节自然度、节奏、追读感和平台适配度。",
        "pages": {
            "AI 腔检测": "optimization.ai_tone_detector",
            "剧情节奏诊断": "optimization.pacing_analyzer",
            "伏笔回收推荐": "optimization.foreshadow_payoff",
            "平台适配器": "optimization.platform_adapter",
        },
    },
    "IP 改编与分发": {
        "icon": "IP",
        "description": "将章节改编成漫画、短剧、视频、小红书、海报提示词。",
        "pages": {
            "章节改编矩阵": "adaptation.adaptation_matrix",
            "漫画分镜": "adaptation.comic_storyboard",
            "短剧脚本": "adaptation.short_drama_script",
            "小红书文案": "adaptation.xiaohongshu_post",
            "海报/角色卡提示词": "adaptation.poster_prompt",
        },
    },
}


PUBLIC_WITHOUT_PROJECT = {
    ("创作启动", "从 0 创建小说"),
    ("创作启动", "项目管理"),
    ("章节创作", "模型与数据设置"),
}


def module_path(short_path: str) -> str:
    return f"app.ui.sections.{short_path}"
