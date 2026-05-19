from __future__ import annotations

import streamlit as st

from app.creative_center import detect_ai_tone_for_chapter, rewrite_ai_tone_for_chapter
from app.db.database import db_session, get_project
from app.quality.novelization_rewriter import novelize_chapter
from app.ui.components.project_selector import project_selector
from app.ui.services import chapter_options


def render(project: str | None = None):
    st.title("AI 腔检测与小说化重写")
    project = project or project_selector()
    if not project:
        st.stop()
    chapters = chapter_options(project)
    if not chapters:
        st.warning("当前项目还没有章节。")
        st.stop()

    labels = [f"第 {c['chapter_number']} 章｜{c['title']}" for c in chapters]
    label = st.selectbox("选择章节", labels)
    chapter = chapters[labels.index(label)]
    with db_session() as conn:
        project_id = int(get_project(conn, project)["id"])
    chapter_id = int(chapter["id"])

    c1, c2, c3 = st.columns(3)
    if c1.button("检测 AI 腔", type="primary", use_container_width=True):
        st.session_state["ai_tone_report"] = detect_ai_tone_for_chapter(project_id, chapter_id)
    if c2.button("整章自然化", use_container_width=True):
        st.session_state["ai_tone_rewrite"] = rewrite_ai_tone_for_chapter(project_id, chapter_id, apply=False)
    if c3.button("小说化重写本章", use_container_width=True):
        st.session_state["novelize_report"] = novelize_chapter(project_id, chapter_id, save_as_new_version=True)
        st.success("已保存小说化新版本，原章节保留。")

    report = st.session_state.get("ai_tone_report")
    if report:
        st.subheader(f"总风险：{report.get('risk_level', 'low').upper()}")
        st.caption("High 不等于整章失败。系统会区分必须修复、建议优化、可保留文学表达和轻小说允许表达。")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("综合分", report.get("overall_score", 0))
        m2.metric("AI 腔密度", f"{report.get('ai_tone_density', 0):.1%}")
        m3.metric("读者影响", report.get("reader_impact", "low"))
        m4.metric("推荐处理", report.get("rewrite_priority", "none"))
        st.write(report.get("summary", ""))
        st.json(report.get("issue_distribution", {}))

        must_fix = [i for i in report.get("issues", []) if not i.get("can_keep") and i.get("severity") == "high"]
        suggested = [i for i in report.get("issues", []) if not i.get("can_keep") and i.get("severity") != "high"]
        keepable = [i for i in report.get("issues", []) if i.get("can_keep")]
        tabs = st.tabs(["必须修复", "建议优化", "可保留表达", "下一章规避建议"])
        with tabs[0]:
            for issue in must_fix[:30]:
                st.error(issue.get("original_text", ""))
                st.caption(issue.get("why_it_feels_ai", ""))
        with tabs[1]:
            for issue in suggested[:30]:
                st.warning(issue.get("original_text", ""))
                st.caption(issue.get("rewrite_suggestion", ""))
        with tabs[2]:
            for issue in keepable[:30]:
                st.info(issue.get("original_text", ""))
                st.caption(issue.get("reason", ""))
        with tabs[3]:
            for item in report.get("generation_prompt_adjustments", []):
                st.write("- " + item)

    rewrite = st.session_state.get("ai_tone_rewrite")
    if rewrite:
        st.subheader("自然化润色预览")
        st.caption(f"修改段落/句子数：{len(rewrite.get('changed_segments', []))}")
        st.text_area("润色版正文", rewrite.get("rewritten_text", ""), height=420)

    novelize_report = st.session_state.get("novelize_report")
    if novelize_report:
        st.subheader("小说化重写报告")
        st.json(novelize_report)
