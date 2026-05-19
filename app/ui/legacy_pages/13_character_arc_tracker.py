import streamlit as st

from app.ui.components.project_selector import project_selector
from app.ui.services import chapter_options, character_options, run_character_arc, run_character_drift, run_character_presence

st.title("人物弧光追踪")
project = project_selector()
if not project:
    st.stop()

characters = character_options(project)
if not characters:
    st.info("暂无人物卡。请先导入章节或从 0 创建小说。")
    st.stop()

labels = [f"{c['id']} - {c['name']} ({c['role'] or '角色'})" for c in characters]
character_id = int(st.selectbox("选择角色", labels).split(" - ")[0])

if st.button("分析人物弧光", type="primary"):
    with st.spinner("正在读取人物卡和章节事实..."):
        st.session_state["arc_report"] = run_character_arc(project, character_id)

if st.session_state.get("arc_report"):
    st.json(st.session_state["arc_report"])

chapters = chapter_options(project)
if chapters:
    labels_ch = [f"{c['chapter_number']} - {c['title']}" for c in chapters]
    chapter = chapters[labels_ch.index(st.selectbox("选择章节检测漂移", labels_ch))]
    if st.button("检测章节人物漂移"):
        st.json(run_character_drift(project, int(chapter["id"])))

with st.expander("重要角色出场间隔"):
    st.dataframe(run_character_presence(project), use_container_width=True)
