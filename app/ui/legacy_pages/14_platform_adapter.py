import streamlit as st

from app.platforms.platform_profiles import BUILTIN_PROFILES
from app.ui.components.project_selector import project_selector
from app.ui.services import chapter_options, run_platform_adapt, run_platform_fit

st.title("平台适配器")
project = project_selector()
if not project:
    st.stop()
chapters = chapter_options(project)
if not chapters:
    st.info("请先导入或生成章节。")
    st.stop()

labels = [f"{c['chapter_number']} - {c['title']}" for c in chapters]
chapter = chapters[labels.index(st.selectbox("选择章节", labels))]
platform = st.selectbox("目标平台", list(BUILTIN_PROFILES.keys()))

if st.button("分析平台适配度", type="primary"):
    st.session_state["platform_report"] = run_platform_fit(project, int(chapter["id"]), platform)
if st.session_state.get("platform_report"):
    st.json(st.session_state["platform_report"])

apply = st.checkbox("保存为新章节版本", value=False)
if st.button("生成平台适配版本"):
    result = run_platform_adapt(project, int(chapter["id"]), platform, apply)
    st.text_area("适配版本/改写方向", result["adapted_text"], height=420)
