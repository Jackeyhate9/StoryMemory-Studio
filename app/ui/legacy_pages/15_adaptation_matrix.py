import json

import streamlit as st

from app.ui.components.project_selector import project_selector
from app.ui.services import chapter_options, run_adaptation_matrix


st.title("章节改编矩阵")
project = project_selector()
if not project:
    st.stop()

st.info("把同一章节改编为漫画分镜、短剧脚本、AI 视频分镜、小红书文案、海报提示词和章节金句。结果会写入改编日志，便于追踪。")

chapters = chapter_options(project)
if not chapters:
    st.info("请先导入或生成章节。")
    st.stop()

labels = [f"{c['chapter_number']} - {c['title']}" for c in chapters]
chapter = chapters[labels.index(st.selectbox("选择章节", labels))]
type_labels = {
    "全部类型": "all",
    "漫画分镜": "comic",
    "短剧脚本": "short_drama",
    "AI 视频分镜": "video",
    "小红书文案": "xiaohongshu",
    "海报/角色卡提示词": "poster",
    "章节金句": "quotes",
}
default_type = st.session_state.pop("adaptation_default_type", "all")
default_label = next((k for k, v in type_labels.items() if v == default_type), "全部类型")
adaptation_label = st.selectbox("改编类型", list(type_labels.keys()), index=list(type_labels.keys()).index(default_label))
adaptation_type = type_labels[adaptation_label]

if st.button("生成改编内容", type="primary"):
    with st.spinner("正在生成改编矩阵..."):
        st.session_state["adaptation_result"] = run_adaptation_matrix(project, int(chapter["id"]), adaptation_type)

result = st.session_state.get("adaptation_result")
if result:
    tabs = st.tabs(["结构化结果", "Markdown 文档"])
    with tabs[0]:
        st.json(result["json"])
        st.download_button(
            "导出 JSON",
            json.dumps(result["json"], ensure_ascii=False, indent=2),
            "adaptation.json",
            "application/json",
        )
    with tabs[1]:
        st.markdown(result["markdown"])
        st.download_button("导出 Markdown", result["markdown"], "adaptation.md", "text/markdown")
