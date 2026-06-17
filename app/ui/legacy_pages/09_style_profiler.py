import json

import streamlit as st

from app.ui.components.project_selector import project_selector
from app.ui.services import analyze_style_for_project, available_provider_options, check_style_similarity, save_style_analysis
from app.style.style_safety import clean_sample_text

st.title("文风学习器")
project = project_selector()
if not project:
    st.stop()

st.info("系统只提取抽象文风特征，不复制原文句子、角色、设定或独特表达。默认不保存完整样章。")

col1, col2 = st.columns(2)
with col1:
    style_name = st.text_input("风格名称", value="快节奏悬疑克制文风")
    source_note = st.text_input("样章来源说明（可选）")
    target_usage = st.multiselect(
        "目标用途",
        ["小说正文", "章节润色", "漫画分镜", "短剧脚本", "小红书推文"],
        default=["小说正文"],
    )
with col2:
    provider_options = available_provider_options()
    provider = st.selectbox(
        "分析模型",
        provider_options,
        index=0,
        format_func=lambda x: {
            "auto": "自动识别（跟随设置）",
            "none": "本地快速分析（不调用模型）",
            "deepseek": "DeepSeek",
            "glm": "智谱 GLM / Z.ai",
            "openai": "OpenAI",
            "openai_compatible": "OpenAI 兼容服务",
            "ollama": "Ollama 本地模型",
        }.get(x, x),
        help="自动识别会优先使用设置页中可用的默认模型；没有配置模型时退回本地统计分析。",
    )
    save_source = st.checkbox("保存完整原文样章", value=False, help="默认不保存完整原文，只保存 hash、短摘录和风格画像。")
    set_default = st.checkbox("设为项目默认文风", value=True)

sample_text = st.text_area("粘贴样章文本", height=240)
uploaded = st.file_uploader("上传样章（txt / md / docx / doc；可多选）", type=["txt", "md", "docx", "doc"], accept_multiple_files=True)

samples = []
if sample_text.strip():
    samples.append(clean_sample_text(sample_text))
for file in uploaded or []:
    suffix = file.name.lower().split(".")[-1]
    try:
        if suffix in {"txt", "md", "doc"}:
            samples.append(clean_sample_text(file.getvalue().decode("utf-8", errors="ignore")))
        elif suffix == "docx":
            from io import BytesIO
            from docx import Document

            doc = Document(BytesIO(file.getvalue()))
            samples.append(clean_sample_text("\n".join(p.text for p in doc.paragraphs if p.text.strip())))
    except Exception as exc:
        st.error(f"读取 {file.name} 失败：{exc}")

if samples:
    st.caption(f"已载入 {len(samples)} 个样章，共 {sum(len(x) for x in samples):,} 字。")

if st.button("分析文风", type="primary", disabled=not samples or not style_name.strip()):
    try:
        with st.spinner("正在分析抽象文风画像..."):
            analysis = analyze_style_for_project(project, style_name, samples, target_usage, source_note, save_source, set_default, provider)
        st.session_state["style_analysis"] = json.dumps(analysis, ensure_ascii=False, indent=2)
        st.success("分析完成。请预览后保存到项目。")
    except Exception as exc:
        st.error(str(exc))

analysis_text = st.session_state.get("style_analysis", "")
if analysis_text:
    analysis = json.loads(analysis_text)
    profile = analysis["profile"]
    tabs = st.tabs(["风格画像", "应该遵守", "必须避免", "安全摘要", "结构化编辑", "测试生成"])
    with tabs[0]:
        st.json(profile)
    with tabs[1]:
        st.write(profile.get("do_rules", []))
    with tabs[2]:
        st.write(profile.get("dont_rules", []))
        st.write(profile.get("forbidden_copy_rules", []))
    with tabs[3]:
        st.text_area("安全风格摘要", profile.get("safe_style_summary", ""), height=160)
    with tabs[4]:
        edited = st.text_area("可编辑风格画像结构化数据", analysis_text, height=520)
        st.session_state["style_analysis"] = edited
    with tabs[5]:
        test_text = st.text_area(
            "输入一段测试生成文本，检查是否过度接近样章",
            value="他推开门，先听见钟声。走廊尽头没有人，只有一盏灯在闪。",
            height=180,
        )
        if st.button("运行相似度保护检查"):
            source = "\n\n".join(analysis.get("input", {}).get("samples", []))
            report = check_style_similarity(source, test_text)
            if report["risk_level"] == "high":
                st.error("相似度风险高，需要重写。")
            elif report["risk_level"] == "medium":
                st.warning("存在中等相似风险，请检查表达。")
            else:
                st.success("风险较低。")
            st.json(report)

    c1, c2 = st.columns(2)
    if c1.button("保存到项目", type="primary"):
        try:
            style_id = save_style_analysis(project, json.loads(st.session_state["style_analysis"]), save_source, set_default)
            st.success(f"风格画像已保存，ID：{style_id}")
        except Exception as exc:
            st.error(str(exc))
    if c2.button("清空当前分析"):
        st.session_state.pop("style_analysis", None)
        st.rerun()
