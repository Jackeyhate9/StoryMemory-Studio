import streamlit as st

from app.ui.components.context_preview import context_preview
from app.ui.components.project_selector import project_selector
from app.ui.services import available_provider_options, build_context, export_chapter_bytes, generate_with_context, save_generated_chapter

st.title("章节生成")
project = project_selector()
if not project:
    st.stop()

st.info("生成结果会先进入下方编辑框，你可以在前端直接修改，再保存为章节或导出为文档/纯文本。")

col1, col2 = st.columns(2)
with col1:
    chapter_number = st.number_input("目标章节编号", min_value=1, step=1)
    mode_label = st.selectbox("生成模式", ["章节大纲", "章节正文", "续写", "改写", "漫画分镜", "短剧脚本", "小红书推广文案"])
    mode_map = {
        "章节大纲": "generate_outline",
        "章节正文": "generate_chapter",
        "续写": "continue",
        "改写": "rewrite",
        "漫画分镜": "comic_adaptation",
        "短剧脚本": "short_drama",
        "小红书推广文案": "xiaohongshu",
    }
    budget_labels = {
        "轻量 32K": "lite",
        "标准 128K": "standard",
        "长上下文 800K": "deepseek_long",
        "全书审计 100万": "full_audit",
    }
    budget_label = st.selectbox(
        "上下文预算",
        list(budget_labels.keys()),
        index=1,
        help="日常生成推荐“标准 128K”；全书审计再用“长上下文 800K”或“全书审计 100万”。",
    )
    budget = budget_labels[budget_label]
    provider = st.selectbox(
        "生成模型",
        [x for x in available_provider_options() if x != "none"],
        format_func=lambda x: {
            "auto": "自动识别（跟随设置）",
            "deepseek": "DeepSeek",
            "glm": "智谱 GLM / Z.ai",
            "openai": "OpenAI",
            "openai_compatible": "OpenAI 兼容服务",
            "ollama": "Ollama 本地模型",
        }.get(x, x),
    )
with col2:
    characters = st.text_input("出场人物（逗号分隔）", placeholder="林舟, 沈青")
    locations = st.text_input("地点（逗号分隔）", placeholder="青岚城, 南街客栈")
    save_title = st.text_input("章节标题", value=f"第{int(chapter_number)}章")
    save_volume = st.text_input("卷名")

goal = st.text_area("本章目标", height=100, placeholder="说明这一章必须完成什么剧情功能。")
outline = st.text_area("本章大纲", height=140, placeholder="按场景写出本章推进顺序。")
extra_instruction = st.text_area("额外要求或待改写文本", height=120)

if st.button("构建上下文", type="primary"):
    context = build_context(
        project,
        int(chapter_number),
        goal,
        outline,
        [x.strip() for x in characters.split(",") if x.strip()],
        [x.strip() for x in locations.split(",") if x.strip()],
        budget,
    )
    st.session_state["context_preview"] = context

context = st.session_state.get("context_preview", "")
if context:
    context_preview(context)

if st.button("生成内容", disabled=not context):
    with st.spinner("正在调用模型生成..."):
        result = generate_with_context(provider, context, mode_map[mode_label], extra_instruction, project=project)
    st.session_state["generated_text"] = result

generated = st.session_state.get("generated_text", "")
if generated:
    st.subheader("生成结果，可直接编辑")
    edited = st.text_area("在这里修改章节正文，然后保存或导出", generated, height=560)
    st.session_state["generated_text"] = edited

    export_cols = st.columns(3)
    for col, fmt, label in zip(export_cols, ["txt", "docx", "doc"], ["导出纯文本", "导出文档", "导出兼容文档"]):
        data, filename, mime = export_chapter_bytes(save_title or f"第{int(chapter_number)}章", edited, int(chapter_number), fmt)
        col.download_button(label, data=data, file_name=filename, mime=mime, use_container_width=True)

    st.warning("保存前建议先到“一致性检查”页面检查穿帮和 AI 腔。")
    if st.button("保存为新章节", type="primary"):
        with st.spinner("正在保存章节并更新记忆库..."):
            extraction = save_generated_chapter(
                project,
                int(chapter_number),
                save_title or f"第{int(chapter_number)}章",
                edited,
                save_volume,
                "none",
            )
        st.success("已保存为章节，并完成本地记忆抽取。")
        st.json(extraction)
