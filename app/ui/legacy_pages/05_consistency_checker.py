import streamlit as st

from app.ui.components.project_selector import project_selector
from app.ui.services import available_provider_options, chapter_options, check_text

st.title("一致性检查")
project = project_selector()
if not project:
    st.stop()

st.info("生成后先检查再入库。系统会重点看人物性格、已知信息、时间线、道具状态、伏笔和 AI 腔表达。")

chapters = chapter_options(project)
source = st.radio("章节来源", ["粘贴文本", "选择已有章节"], horizontal=True)
chapter_number = st.number_input("章节编号", min_value=1, step=1)
goal = st.text_area("章节目标", placeholder="这一章原本应该完成什么？")
provider = st.selectbox(
    "检查模型",
    available_provider_options(),
    format_func=lambda x: {
        "auto": "自动识别（跟随设置）",
        "none": "本地基础检查（不调用模型）",
        "deepseek": "DeepSeek",
        "openai": "OpenAI",
        "openai_compatible": "OpenAI 兼容服务",
        "ollama": "Ollama 本地模型",
    }.get(x, x),
)

text = ""
if source == "选择已有章节" and chapters:
    labels = [f"{c['chapter_number']} - {c['title']}" for c in chapters]
    selected = st.selectbox("选择章节", labels)
    item = chapters[labels.index(selected)]
    chapter_number = item["chapter_number"]
    text = st.text_area("章节正文", item["content"], height=360)
else:
    text = st.text_area("粘贴待检查章节", height=360)

if st.button("检查穿帮", type="primary", disabled=not text.strip()):
    with st.spinner("正在检查一致性..."):
        report = check_text(project, int(chapter_number), text, goal, provider)
    if report.get("passed"):
        st.success("未发现严重问题。")
    else:
        st.error("发现需要处理的问题。")
    st.json(report)
