import streamlit as st

from app.ui.components.project_selector import project_selector
from app.ui.components.result_panel import result_panel
from app.ui.services import (
    available_provider_options,
    import_chapter_batch,
    import_chapter_text,
    read_uploaded_text,
    split_chapters_from_text,
)


st.title("章节导入")
project = project_selector()
if not project:
    st.stop()

st.info("支持粘贴正文、上传 txt/md/docx，并可把已有小说全文按“第 X 章”自动拆分后批量导入。导入后会写入章节表并抽取章节摘要、事实、人物、伏笔和时间线。")

provider = st.selectbox(
    "记忆抽取方式",
    available_provider_options(),
    format_func=lambda x: {
        "auto": "自动识别",
        "none": "本地启发式，不调用模型",
        "deepseek": "DeepSeek",
        "glm": "智谱 GLM / Z.ai",
        "openai": "OpenAI",
        "openai_compatible": "OpenAI 兼容服务",
        "ollama": "Ollama 本地模型",
    }.get(x, x),
)

mode = st.radio("导入模式", ["单章导入", "批量拆分导入"], horizontal=True)
uploaded = st.file_uploader("上传章节文件（txt / md / docx）", type=["txt", "md", "docx"], accept_multiple_files=(mode == "批量拆分导入"))

if mode == "单章导入":
    col1, col2 = st.columns(2)
    with col1:
        number = st.number_input("章节编号", min_value=1, step=1)
        title = st.text_input("章节标题")
    with col2:
        volume = st.text_input("卷名")
    uploaded_text = ""
    if uploaded:
        file = uploaded[0] if isinstance(uploaded, list) else uploaded
        uploaded_text = read_uploaded_text(file.name, file.getvalue())
        if not title:
            title = file.name.rsplit(".", 1)[0]
    content = st.text_area("章节正文", value=uploaded_text, height=360)
    if st.button("导入章节并抽取记忆", type="primary", disabled=not content.strip()):
        with st.spinner("正在导入章节并抽取长期记忆..."):
            result = import_chapter_text(project, int(number), title or f"第 {int(number)} 章", content, volume, provider)
        st.success("导入完成。")
        tabs = st.tabs(["摘要", "人物", "章节事实", "伏笔", "时间线"])
        with tabs[0]:
            result_panel("章节摘要", result.get("summary", {}))
        with tabs[1]:
            result_panel("抽取人物", result.get("characters", []))
        with tabs[2]:
            result_panel("章节事实", result.get("facts", []))
        with tabs[3]:
            result_panel("伏笔", result.get("foreshadows", []))
        with tabs[4]:
            result_panel("时间线事件", result.get("timeline_events", []))
else:
    start_number = st.number_input("起始章节编号", min_value=1, step=1)
    volume = st.text_input("卷名")
    pasted = st.text_area("也可以粘贴整本或多章文本", height=260)
    combined = pasted
    if uploaded:
        chunks = []
        for file in uploaded:
            chunks.append(read_uploaded_text(file.name, file.getvalue()))
        combined = "\n\n".join(chunks) + ("\n\n" + pasted if pasted.strip() else "")
    chapters = split_chapters_from_text(combined) if combined.strip() else []
    st.caption(f"预览拆分结果：{len(chapters)} 章")
    if chapters:
        st.dataframe([{"序号": i + int(start_number), "标题": c["title"], "字数": len(c["content"])} for i, c in enumerate(chapters)], use_container_width=True, hide_index=True)
    if st.button("批量导入并抽取记忆", type="primary", disabled=not chapters):
        with st.spinner("正在批量导入，章节较多时会需要一点时间..."):
            results = import_chapter_batch(project, int(start_number), chapters, volume, provider)
        st.success(f"已导入 {len(results)} 章。")
        st.json(results[:5])
