from __future__ import annotations

import importlib

import streamlit as st

from app.ui.navigation import NAVIGATION, PUBLIC_WITHOUT_PROJECT, module_path
from app.ui.services import RESOURCE_ROOT, dashboard_snapshot, health_snapshot, list_projects


SECTION_ACCENTS = {
    "创作启动": "#2563eb",
    "记忆中枢": "#0f766e",
    "章节创作": "#7c3aed",
    "一致性管理": "#c2410c",
    "质量优化": "#15803d",
    "IP 改编与分发": "#be123c",
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --story-bg: #f4f7fb;
          --story-panel: #ffffff;
          --story-ink: #172033;
          --story-muted: #64748b;
          --story-line: #dbe3ef;
          --story-line-strong: #cbd5e1;
          --story-shadow: 0 16px 40px rgba(15, 23, 42, .07);
        }
        .stApp { background: linear-gradient(180deg, #f8fbff 0%, #f4f7fb 280px, #f4f7fb 100%); color: var(--story-ink); }
        #MainMenu, footer, header { visibility: hidden; }
        .block-container { padding-top: 1rem; max-width: 1320px; }
        section[data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--story-line); box-shadow: 8px 0 28px rgba(15, 23, 42, .04); }
        section[data-testid="stSidebar"] div[role="radiogroup"] label { border-radius: 8px; padding: .2rem .35rem; }
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: #f1f5f9; }
        .story-sidebar-brand { padding: .85rem; border: 1px solid var(--story-line); border-radius: 8px; background: #f8fafc; margin-bottom: .85rem; }
        .story-sidebar-brand h2 { margin: 0; font-size: 1.08rem; line-height: 1.25; letter-spacing: 0; }
        .story-sidebar-brand p { margin: .35rem 0 0 0; color: var(--story-muted); font-size: .82rem; line-height: 1.45; }
        .story-topbar { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; margin-bottom: 1rem; }
        .story-title h1 { font-size: 1.75rem; line-height: 1.2; margin: 0; letter-spacing: 0; }
        .story-title p { margin: .4rem 0 0 0; color: var(--story-muted); font-size: .95rem; }
        .story-pill { border: 1px solid var(--story-line); background: #fff; border-radius: 999px; padding: .42rem .75rem; color: var(--story-muted); font-size: .84rem; max-width: 520px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .story-hero { border: 1px solid var(--story-line); background: #fff; box-shadow: var(--story-shadow); border-radius: 8px; padding: 1.1rem 1.15rem; margin-bottom: 1rem; }
        .story-hero h2 { margin: 0; font-size: 1.25rem; letter-spacing: 0; }
        .story-hero p { color: var(--story-muted); margin: .45rem 0 0 0; line-height: 1.65; }
        .story-safe { border: 1px solid #bbf7d0; border-left: 4px solid #15803d; background: #f0fdf4; padding: .75rem .9rem; border-radius: 8px; color: #14532d; font-size: .92rem; margin: .75rem 0 1rem 0; }
        .story-card { background: #fff; border: 1px solid var(--story-line); border-radius: 8px; padding: 1rem; min-height: 178px; box-shadow: 0 8px 24px rgba(15, 23, 42, .045); transition: border-color .12s ease, box-shadow .12s ease, transform .12s ease; }
        .story-card:hover { border-color: var(--story-line-strong); box-shadow: var(--story-shadow); transform: translateY(-1px); }
        .story-card-top { display: flex; align-items: center; gap: .65rem; margin-bottom: .55rem; }
        .story-icon { width: 2.05rem; height: 2.05rem; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; color: #fff; font-size: .78rem; font-weight: 750; }
        .story-card h3 { margin: 0; font-size: 1.03rem; letter-spacing: 0; }
        .story-card p { color: var(--story-muted); font-size: .9rem; margin: 0 0 .65rem 0; line-height: 1.58; }
        .story-tags { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .65rem; }
        .story-tag { display: inline-block; border: 1px solid var(--story-line); background: #f8fafc; color: #475569; border-radius: 999px; padding: .2rem .48rem; font-size: .78rem; line-height: 1.2; }
        .story-workflow { background: #fff; border: 1px solid var(--story-line); border-radius: 8px; padding: 1rem; margin-top: .8rem; }
        .story-workflow h3 { margin: 0 0 .75rem 0; font-size: 1rem; }
        .story-muted-line { color: var(--story-muted); font-size: .9rem; line-height: 1.65; margin: -.25rem 0 .85rem 0; }
        .story-tech-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .7rem; }
        .story-mini-card { border: 1px solid var(--story-line); border-radius: 8px; padding: .75rem; background: #f8fafc; min-height: 105px; }
        .story-mini-card b { display: block; color: var(--story-ink); font-size: .9rem; margin-bottom: .35rem; }
        .story-mini-card span { display: block; color: var(--story-muted); font-size: .8rem; line-height: 1.55; }
        .story-support-caption { color: var(--story-muted); font-size: .86rem; line-height: 1.65; margin-top: .35rem; }
        .story-steps { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .7rem; }
        .story-step { border: 1px solid var(--story-line); border-radius: 8px; padding: .75rem; background: #f8fafc; }
        .story-step b { display: block; font-size: .9rem; margin-bottom: .3rem; }
        .story-step span { color: var(--story-muted); font-size: .82rem; line-height: 1.55; }
        .story-metric-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .8rem; margin: .95rem 0 1.25rem 0; }
        .story-metric { background: #fff; border: 1px solid var(--story-line); border-radius: 8px; padding: .85rem .9rem; box-shadow: 0 8px 22px rgba(15, 23, 42, .04); min-width: 0; }
        .story-metric span { display: block; color: var(--story-muted); font-size: .8rem; margin-bottom: .35rem; }
        .story-metric b { display: block; font-size: 1.28rem; line-height: 1.22; letter-spacing: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .stButton > button { border-radius: 8px; font-weight: 650; border-color: var(--story-line-strong); min-height: 2.35rem; }
        .stButton > button:hover { border-color: #2563eb; color: #1d4ed8; }
        .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div { border-radius: 8px; }
        @media (max-width: 900px) {
          .story-topbar { flex-direction: column; }
          .story-steps { grid-template-columns: 1fr; }
          .story-metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .story-pill { max-width: 100%; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _accent(section: str) -> str:
    return SECTION_ACCENTS.get(section, "#2563eb")


def render_topbar(section: str | None = None, page: str | None = None) -> None:
    health = health_snapshot()
    subtitle = f"{section} / {page}" if section and page else "本地优先的长篇 IP 创作中控台"
    st.markdown(
        f"""
        <div class="story-topbar">
          <div class="story-title">
            <h1>长篇记忆小说</h1>
            <p>{subtitle}</p>
          </div>
          <div class="story-pill">数据位置：{health["data_dir"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[str | None, str, str]:
    st.sidebar.markdown(
        """
        <div class="story-sidebar-brand">
          <h2>长篇记忆小说</h2>
          <p>结构化记忆、章节生成、质量优化和 IP 改编都在这里完成。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    projects = list_projects()
    project = None
    if projects:
        names = [p["name"] for p in projects]
        current = st.session_state.get("project", names[0])
        index = names.index(current) if current in names else 0
        project = st.sidebar.selectbox("当前项目", names, index=index, key="nav_project")
        st.session_state["project"] = project
    else:
        st.sidebar.info("还没有项目。请先从 0 创建小说，或进入项目管理导入已有作品。")

    sections = list(NAVIGATION.keys())
    default_section = st.session_state.get("nav_section", sections[0])
    section = st.sidebar.radio(
        "一级板块",
        sections,
        index=sections.index(default_section) if default_section in sections else 0,
    )
    st.session_state["nav_section"] = section

    info = NAVIGATION[section]
    st.sidebar.caption(f'{info["icon"]} · {info["description"]}')
    page_names = list(info["pages"].keys())
    default_page = st.session_state.get("nav_page", page_names[0])
    if default_page not in page_names:
        default_page = page_names[0]
    page = st.sidebar.selectbox("子功能", page_names, index=page_names.index(default_page), key=f"sub_{section}")
    st.session_state["nav_page"] = page
    st.sidebar.divider()
    st.sidebar.caption("推荐顺序：启动创作 -> 建立记忆 -> 生成章节 -> 检查一致性 -> 优化质量 -> 改编分发")
    return project, section, page


def _render_dashboard_intro(project: str | None, snapshot: dict) -> None:
    title = f"继续创作《{project}》" if project else "先建立你的第一个小说项目"
    body = (
        "系统会从章节、人物、伏笔、时间线和文风中沉淀长期记忆，生成新章节前再按优先级构建上下文。"
        if project
        else "你可以从 0 创建小说，也可以导入已有作品，让系统先抽取人物、事实、伏笔和文风。"
    )
    st.markdown(
        f"""
        <div class="story-hero">
          <h2>{title}</h2>
          <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if snapshot["next_action"]:
        st.markdown(f'<div class="story-safe">{snapshot["next_action"]}</div>', unsafe_allow_html=True)


def _render_workflow() -> None:
    st.markdown(
        """
        <div class="story-workflow">
          <h3>常用工作流</h3>
          <div class="story-steps">
            <div class="story-step"><b>1. 创作启动</b><span>从 0 创建小说，或导入已有章节和设定。</span></div>
            <div class="story-step"><b>2. 记忆沉淀</b><span>抽取人物、事实、伏笔、时间线和文风画像。</span></div>
            <div class="story-step"><b>3. 章节生产</b><span>构建上下文，生成、编辑并导出章节。</span></div>
            <div class="story-step"><b>4. 优化分发</b><span>检测 AI 腔、节奏和平台适配，再改编成多种 IP 内容。</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_metrics(project: str | None, snapshot: dict) -> None:
    values = [
        ("当前项目", project or "未创建"),
        ("章节数", str(snapshot["chapter_count"])),
        ("人物数", str(snapshot["character_count"])),
        ("未回收伏笔", str(snapshot["open_foreshadow_count"])),
        ("最近生成", snapshot["last_generation"] or "暂无"),
    ]
    cards = "".join(
        f'<div class="story-metric" title="{value}"><span>{label}</span><b>{value}</b></div>'
        for label, value in values
    )
    st.markdown(f'<div class="story-metric-grid">{cards}</div>', unsafe_allow_html=True)


def render_dashboard(project: str | None) -> None:
    render_topbar()
    snapshot = dashboard_snapshot(project)
    _render_dashboard_intro(project, snapshot)
    _render_metrics(project, snapshot)
    _render_tech_stack()

    st.subheader("功能板块")
    items = list(NAVIGATION.items())
    for start in range(0, len(items), 3):
        cols = st.columns(3)
        for col, (section, info) in zip(cols, items[start : start + 3]):
            with col:
                primary = list(info["pages"].keys())[:4]
                accent = _accent(section)
                tags = "".join(f'<span class="story-tag">{name}</span>' for name in primary)
                st.markdown(
                    f"""
                    <div class="story-card">
                      <div class="story-card-top">
                        <span class="story-icon" style="background:{accent};">{info["icon"]}</span>
                        <h3>{section}</h3>
                      </div>
                      <p>{info["description"]}</p>
                      <div class="story-tags">{tags}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(f"进入{section}", key=f"go_{section}", use_container_width=True):
                    st.session_state["nav_section"] = section
                    st.session_state["nav_page"] = primary[0]
                    st.rerun()

    _render_workflow()
    _render_support_info()


def _render_tech_stack() -> None:
    tech_items = [
        ("本地数据", "SQLite + SQLAlchemy，项目数据默认保存在本机 data/ 目录。"),
        ("长上下文编排", "Context Builder 按 S/A/B/C/D 优先级组织 DeepSeek 百万 token 级上下文。"),
        ("模型接入", "支持 DeepSeek、OpenAI-compatible、OpenAI 与 Ollama 本地模型。"),
        ("前端界面", "Streamlit 本地 Web UI，可通过 PyInstaller 打包为 Windows exe。"),
        ("结构化校验", "Pydantic 校验 LLM JSON 输出，并带有 JSON 修复机制。"),
        ("导出能力", "python-docx 导出 docx，支持 md、txt、json 等文本资产。"),
        ("质量治理", "AI 腔检测、humanizer-zh、小说化重写、节奏诊断与一致性检查。"),
        ("IP 改编", "章节可转漫画分镜、短剧脚本、视频分镜、小红书文案和海报提示词。"),
    ]
    cards = "".join(
        f"""
        <div class="story-mini-card">
          <b>{title}</b>
          <span>{body}</span>
        </div>
        """
        for title, body in tech_items
    )
    st.markdown(
        f"""
        <div class="story-workflow">
          <h3>技术架构</h3>
          <p class="story-muted-line">
            StoryMemory Studio 使用“本地结构化记忆库 + 长上下文 Prompt 编排 + 多模型接入 + 质量反馈闭环”的架构，
            让长篇创作既能保留可编辑的事实来源，也能利用 DeepSeek 等长上下文模型做全局理解与一致性检查。
          </p>
          <div class="story-tech-grid">{cards}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_support_info() -> None:
    reward_qr = RESOURCE_ROOT / "app" / "ui" / "assets" / "wechat_reward_qr.jpg"
    contact_qr = RESOURCE_ROOT / "app" / "ui" / "assets" / "wechat_contact_qr.jpg"
    st.markdown(
        """
        <div class="story-workflow">
          <h3>支持与交流</h3>
          <p class="story-muted-line">
            如果 StoryMemory Studio 帮你节省了长篇创作和记忆整理时间，欢迎赞赏支持。
            使用中遇到问题、想交流长篇小说 AI 工作流、反馈 bug 或提出功能建议，也可以扫码添加交流。
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_reward, col_contact = st.columns(2)
    with col_reward:
        if reward_qr.exists():
            st.image(str(reward_qr), caption="赞赏支持：推荐使用微信支付", width=300)
        else:
            st.info("赞赏二维码资源未找到。")
        st.markdown('<div class="story-support-caption">你的支持会用于继续维护本地创作工具、长上下文记忆优化和 Windows 发布包。</div>', unsafe_allow_html=True)
    with col_contact:
        if contact_qr.exists():
            st.image(str(contact_qr), caption="交流反馈：扫码添加作者微信", width=300)
        else:
            st.info("交流二维码资源未找到。")
        st.markdown('<div class="story-support-caption">添加时建议备注：StoryMemory。欢迎反馈使用体验、模型适配问题和长篇创作需求。</div>', unsafe_allow_html=True)


def render_selected_page(project: str | None, section: str, page: str) -> None:
    render_topbar(section, page)
    if not project and (section, page) not in PUBLIC_WITHOUT_PROJECT:
        st.warning("请先创建或选择项目。你可以进入“创作启动 / 从 0 创建小说”或“项目管理”。")
        return
    short_path = NAVIGATION[section]["pages"][page]
    try:
        module = importlib.import_module(module_path(short_path))
        module.render(project)
    except Exception as exc:
        st.error(f"页面加载失败：{page}")
        st.exception(exc)
