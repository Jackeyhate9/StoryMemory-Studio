import json

import streamlit as st

from app.ui.components.project_selector import project_selector
from app.ui.services import archive_project, create_or_update_project, delete_project, list_projects, project_by_name


st.title("项目管理")
project = project_selector()

st.info("先创建或选择一个小说项目。后续章节、记忆、文风、检测报告都会绑定到当前项目。")

current = project_by_name(project) if project else None

with st.form("project_form"):
    st.subheader("创建或编辑项目")
    name = st.text_input("项目标识", value=(current or {}).get("name", project or "demo_project"), help="用于本地数据库识别，建议使用英文、拼音或短横线。")
    title = st.text_input("作品名称", value=(current or {}).get("title", ""))
    description = st.text_area("小说简介", value=(current or {}).get("description", ""), height=120)
    col1, col2 = st.columns(2)
    with col1:
        genre = st.text_input("作品类型", value=(current or {}).get("genre", ""))
    with col2:
        platforms = ["番茄小说", "起点中文网", "晋江文学城", "七猫", "短剧", "漫画分镜", "小红书推文", "AI 视频分镜", "其他"]
        current_platform = (current or {}).get("target_platform") or "番茄小说"
        platform = st.selectbox(
            "目标平台",
            platforms,
            index=platforms.index(current_platform) if current_platform in platforms else 0,
        )
    default_model = st.text_input("默认模型", value=json.loads((current or {}).get("metadata_json") or "{}").get("default_model", ""))
    if st.form_submit_button("保存项目", type="primary"):
        create_or_update_project(name, title or name, description, genre, platform, default_model)
        st.session_state["project"] = name
        st.success("项目已保存。")
        st.rerun()

st.subheader("项目列表")
projects = list_projects()
if projects:
    st.dataframe(projects, use_container_width=True, hide_index=True)
else:
    st.caption("还没有项目。")

if project and current:
    st.subheader("当前项目状态")
    c1, c2, c3 = st.columns(3)
    c1.metric("项目状态", current.get("status") or "active")
    c2.metric("作品类型", current.get("genre") or "未设置")
    c3.metric("目标平台", current.get("target_platform") or "未设置")

    with st.expander("危险操作", expanded=False):
        st.warning("归档不会删除数据；删除会移除该项目及其章节、记忆和日志。建议先进入“备份与恢复”创建备份。")
        if st.button("归档当前项目"):
            archive_project(project)
            st.success("项目已归档。")
            st.rerun()
        confirm = st.checkbox(f"我确认删除项目：{project}")
        if st.button("删除当前项目", disabled=not confirm, type="primary"):
            delete_project(project)
            st.session_state.pop("project", None)
            st.success("项目已删除。")
            st.rerun()
