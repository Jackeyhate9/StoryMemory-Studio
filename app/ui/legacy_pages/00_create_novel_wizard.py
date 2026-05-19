import json
from pathlib import Path

import streamlit as st

from app.creation.preview_store import save_preview_text
from app.creation.seed_parser import parse_seed
from app.creation.wizard import commit_preview_text, create_preview, regenerate_preview_section
from app.db.database import db_session, get_project
from app.export.bible_export import export_bible
from app.ui.services import available_provider_options, resolve_auto_provider

st.title("从 0 创建小说")
st.info("没有已有章节也可以开始。先填写少量基础设定，系统会生成小说 Bible 和第一章草稿；确认前不会写入正式数据库。")

mode_label = st.radio("输入模式", ["最低输入", "专业输入"], horizontal=True)
mode = "minimal" if mode_label == "最低输入" else "pro"

provider = st.selectbox(
    "生成模型",
    available_provider_options(),
    format_func=lambda x: {
        "auto": "自动识别（跟随设置）",
        "none": "本地启发式（不调用模型）",
        "deepseek": "DeepSeek",
        "openai": "OpenAI",
        "openai_compatible": "OpenAI 兼容服务",
        "ollama": "Ollama 本地模型",
    }.get(x, x),
    help="自动识别会优先使用设置页中可用的默认模型；没有配置模型时退回本地启发式生成。",
)

with st.form("create_novel_seed"):
    st.subheader("基础设定")
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("小说标题", value="死后三日前")
        genre = st.text_input("小说类型", value="都市悬疑时间循环")
        platform = st.text_input("目标平台", value="番茄小说")
        premise = st.text_area("一句话核心设定", value="男主每死一次都会回到三天前，但每次都会失去一个关于女主的记忆。")
        protagonist = st.text_area("主角基础信息", value="陆沉，27岁，前刑警，冷静克制，有创伤。")
    with col2:
        goal = st.text_area("主角目标", value="查清女主死亡真相，打破循环。")
        selling_points = st.text_input("核心爽点", value="反转,推理,时间循环,情感拉扯")
        avoid = st.text_input("不想要的内容", value="不要系统,不要后宫,不要无脑金手指")
        length = st.text_input("预计章节数", value="100章")
        style = st.text_area("文风参考", value="快节奏，悬疑感强，情绪克制，章节末尾有钩子。")

    pro_payload = {}
    if mode == "pro":
        st.subheader("专业设定")
        c1, c2 = st.columns(2)
        with c1:
            pro_payload["target_reader"] = st.text_input("目标读者")
            pro_payload["word_count"] = st.number_input("预计字数", min_value=0, step=10000)
            pro_payload["chapter_word_count"] = st.number_input("单章字数", min_value=500, value=2500, step=500)
            pro_payload["core_conflict"] = st.text_area("核心矛盾")
            pro_payload["story_highlights"] = st.text_area("故事看点")
            pro_payload["major_characters"] = st.text_area("主要角色设定")
        with c2:
            pro_payload["world_setting"] = st.text_area("世界观设定")
            pro_payload["ability_system"] = st.text_area("能力体系")
            pro_payload["organizations"] = st.text_area("势力组织")
            pro_payload["opening_event"] = st.text_area("开局事件")
            pro_payload["first_volume_climax"] = st.text_area("第一卷高潮")
            pro_payload["midpoint_twist"] = st.text_area("中期反转")
            pro_payload["ending_direction"] = st.text_area("结局方向")
            pro_payload["hard_rules"] = st.text_area("不能违背的硬设定")

    submitted = st.form_submit_button("生成小说设定", type="primary")

if submitted:
    try:
        seed = parse_seed(
            mode=mode,
            title=title,
            genre=genre,
            platform=platform,
            premise=premise,
            protagonist=protagonist,
            goal=goal,
            selling_points=selling_points,
            avoid=avoid,
            length=length,
            style=style,
            **pro_payload,
        )
        with st.spinner("正在生成小说 Bible 和第一章草稿..."):
            preview = create_preview(seed, resolve_auto_provider(provider))
        st.session_state["create_seed"] = seed.model_dump()
        st.session_state["create_preview_path"] = preview["preview_path"]
        st.session_state["create_preview_text"] = preview["result"].model_dump_json(indent=2)
        st.success("生成完成。请先预览和编辑，确认后再写入 Story Memory。")
    except Exception as exc:
        st.error(str(exc))

preview_text = st.session_state.get("create_preview_text", "")
if preview_text:
    data = json.loads(preview_text)
    st.subheader("预览")
    tabs = st.tabs(["项目简介", "世界观", "主要人物", "人物关系", "伏笔", "时间线", "前 10 章章纲", "第一章草稿", "结构化编辑"])
    with tabs[0]:
        st.json(data["project"])
    with tabs[1]:
        st.json({"world_rules": data.get("world_rules", []), "locations": data.get("locations", []), "organizations": data.get("organizations", []), "abilities": data.get("abilities", [])})
    with tabs[2]:
        st.json(data.get("characters", []))
    with tabs[3]:
        st.json(data.get("relationships", []))
    with tabs[4]:
        st.json(data.get("foreshadows", []))
    with tabs[5]:
        st.json(data.get("timeline_events", []))
    with tabs[6]:
        st.json(data.get("chapter_outlines", []))
    with tabs[7]:
        first = data.get("first_chapter", {})
        first["content"] = st.text_area("第一章正文草稿，可直接修改", value=first.get("content", ""), height=420)
        data["first_chapter"] = first
        st.session_state["create_preview_text"] = json.dumps(data, ensure_ascii=False, indent=2)
    with tabs[8]:
        edited = st.text_area("完整结构化预览，可编辑后写入", value=st.session_state["create_preview_text"], height=560)
        st.session_state["create_preview_text"] = edited

    st.subheader("重新生成")
    seed = parse_seed(**st.session_state.get("create_seed", {}))
    regen_cols = st.columns(4)
    if regen_cols[0].button("重新生成全部"):
        with st.spinner("正在重新生成全部..."):
            preview = create_preview(seed, resolve_auto_provider(provider))
        st.session_state["create_preview_path"] = preview["preview_path"]
        st.session_state["create_preview_text"] = preview["result"].model_dump_json(indent=2)
        st.rerun()
    for col, section, label in [
        (regen_cols[1], "characters", "局部重新生成角色"),
        (regen_cols[2], "world", "局部重新生成世界观"),
        (regen_cols[3], "outline", "局部重新生成章纲"),
    ]:
        if col.button(label):
            with st.spinner(f"正在{label}..."):
                path = save_preview_text(st.session_state["create_preview_text"], data["project"]["title"])
                preview = regenerate_preview_section(seed, path, section, resolve_auto_provider(provider))
            st.session_state["create_preview_path"] = preview["preview_path"]
            st.session_state["create_preview_text"] = preview["result"].model_dump_json(indent=2)
            st.rerun()

    st.subheader("确认写入")
    output_project = st.text_input("项目标识", value=data["project"]["title"])
    st.warning("点击写入后才会创建正式项目、写入记忆库和第一章。")
    if st.button("写入 Story Memory", type="primary"):
        try:
            with st.spinner("正在写入数据库，并构建第二章上下文..."):
                committed = commit_preview_text(st.session_state["create_preview_text"], output_project, resolve_auto_provider(provider))
            st.session_state["project"] = committed["project"]
            st.session_state["second_context_after_create"] = committed["second_chapter_context"]
            st.success(f"已创建项目：{committed['project']}。第一章已写入，第二章上下文已生成。")
        except Exception as exc:
            st.error(str(exc))

if st.session_state.get("second_context_after_create"):
    with st.expander("第二章上下文预览", expanded=True):
        st.text_area("Context Builder 输出", st.session_state["second_context_after_create"], height=360)
    if st.button("导出小说设定包"):
        try:
            project_name = st.session_state["project"]
            out = Path("exports") / project_name
            with db_session() as conn:
                p = get_project(conn, project_name)
                export_bible(conn, p["id"], out)
            st.success(f"已导出到：{out}")
        except Exception as exc:
            st.error(str(exc))
