import streamlit as st

from app.pacing.pacing_rewriter import pacing_directions
from app.ui.components.project_selector import project_selector
from app.ui.services import chapter_options, run_pacing

st.title("剧情节奏诊断")
project = project_selector()
if not project:
    st.stop()
chapters = chapter_options(project)
if not chapters:
    st.info("请先导入或生成章节。")
    st.stop()

labels = [f"{c['chapter_number']} - {c['title']}" for c in chapters]
chapter = chapters[labels.index(st.selectbox("选择章节", labels))]

if st.button("诊断剧情节奏", type="primary"):
    with st.spinner("正在分析开头、冲突、中段、结尾钩子..."):
        st.session_state["pacing_report"] = run_pacing(project, int(chapter["id"]))

report = st.session_state.get("pacing_report")
if report:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("章节评分", report["chapter_score"])
    c2.metric("开头钩子", report["opening_hook_score"])
    c3.metric("核心冲突", report["conflict_score"])
    c4.metric("结尾钩子", report["ending_hook_score"])
    st.json(report)
    st.subheader("三个优化方向")
    for name, direction in pacing_directions().items():
        st.write(f"**{name}**：{direction}")
