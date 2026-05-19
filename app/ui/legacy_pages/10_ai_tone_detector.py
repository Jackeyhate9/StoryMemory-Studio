import streamlit as st

from app.ui.components.project_selector import project_selector
from app.ui.services import chapter_options, run_ai_tone, run_ai_tone_rewrite

st.title("AI 腔检测")
project = project_selector()
if not project:
    st.stop()

chapters = chapter_options(project)
if not chapters:
    st.info("请先导入或生成章节。")
    st.stop()

labels = [f"{c['chapter_number']} - {c['title']}" for c in chapters]
selected = st.selectbox("选择章节", labels)
chapter = chapters[labels.index(selected)]

if st.button("检测 AI 腔", type="primary"):
    with st.spinner("正在检测模板句、解释性台词和直译腔..."):
        st.session_state["ai_tone_report"] = run_ai_tone(project, int(chapter["id"]))

report = st.session_state.get("ai_tone_report")
if report:
    st.metric("自然度评分", report["overall_score"])
    st.write("风险等级：", report["risk_level"])
    st.json(report)
    apply = st.checkbox("保存为新章节版本", value=False)
    if st.button("一键自然化改写"):
        with st.spinner("正在生成自然化版本..."):
            result = run_ai_tone_rewrite(project, int(chapter["id"]), apply)
        st.success("改写完成。原章节已保留。")
        st.text_area("自然化改写结果", result["rewritten_text"], height=420)
