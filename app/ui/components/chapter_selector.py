from __future__ import annotations

import streamlit as st

from app.ui.services import chapter_options


def chapter_selector(project: str, label: str = "选择章节") -> dict | None:
    chapters = chapter_options(project)
    if not chapters:
        st.info("当前项目还没有章节。请先导入或生成章节。")
        return None
    labels = [f"{c['chapter_number']} - {c['title']}" for c in chapters]
    selected = st.selectbox(label, labels)
    return chapters[labels.index(selected)]
