from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.db.database import db_session, get_project
from app.export.docx_export import export_project_docx
from app.ui.components.project_selector import project_selector
from app.ui.services import (
    chapter_options,
    delete_chapter,
    export_all_chapters_json,
    export_all_chapters_markdown,
    export_chapter_bytes,
    get_chapter,
    update_chapter,
)


def render(project: str | None = None):
    st.title("章节编辑与导出")
    project = project or project_selector()
    if not project:
        st.stop()

    st.info("这里可以直接修改已保存章节，也可以导出单章、全书 Markdown/JSON，或一键导出包含设定附录的完整 docx。")

    chapters = chapter_options(project)
    if not chapters:
        st.warning("当前项目还没有章节。请先导入或生成章节。")
        st.stop()

    labels = [f"第 {item['chapter_number']} 章｜{item['title']}" for item in chapters]
    selected = st.selectbox("选择章节", labels)
    chapter_stub = chapters[labels.index(selected)]
    chapter = get_chapter(project, int(chapter_stub["id"])) or chapter_stub

    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("章节标题", value=chapter.get("title", ""))
    with col2:
        volume = st.text_input("卷名", value=chapter.get("volume", ""))
    outline = st.text_area("章节大纲", value=chapter.get("outline", ""), height=100)
    content = st.text_area("章节正文", value=chapter.get("content", ""), height=560)

    save_cols = st.columns([1, 1, 1, 1, 1])
    if save_cols[0].button("保存修改", type="primary", use_container_width=True):
        update_chapter(project, int(chapter["id"]), title, content, volume, outline)
        st.success("章节修改已保存。")
        st.rerun()

    for col, fmt, label in zip(save_cols[1:], ["txt", "md", "docx", "json"], ["导出 TXT", "导出 Markdown", "导出单章 DOCX", "导出 JSON"]):
        data, filename, mime = export_chapter_bytes(title, content, int(chapter["chapter_number"]), fmt)
        col.download_button(label, data=data, file_name=filename, mime=mime, use_container_width=True)

    with st.expander("全书导出与危险操作", expanded=False):
        md_data, md_name, md_mime = export_all_chapters_markdown(project)
        json_data, json_name, json_mime = export_all_chapters_json(project)
        c1, c2, c3 = st.columns(3)
        c1.download_button("导出全书 Markdown", md_data, file_name=md_name, mime=md_mime, use_container_width=True)
        c2.download_button("导出全书 JSON", json_data, file_name=json_name, mime=json_mime, use_container_width=True)
        if c3.button("生成完整 DOCX", use_container_width=True):
            with db_session() as conn:
                p = get_project(conn, project)
                output = Path("exports") / f"{p['title'] or p['name']}_完整导出.docx"
                path = export_project_docx(conn, int(p["id"]), output)
            st.success(f"DOCX 已生成：{path}")

        st.divider()
        st.warning("删除章节会同时删除该章节摘要、事实等关联数据。建议先备份。")
        confirm = st.checkbox("确认删除当前章节")
        if st.button("删除当前章节", disabled=not confirm):
            delete_chapter(project, int(chapter["id"]))
            st.success("章节已删除。")
            st.rerun()
