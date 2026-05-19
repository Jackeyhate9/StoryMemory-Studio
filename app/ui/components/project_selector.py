import streamlit as st

from app.ui.services import list_projects


def project_selector() -> str | None:
    projects = list_projects()
    if not projects:
        st.info("还没有小说项目，请先进入“项目管理”创建一个项目。")
        return None
    names = [p["name"] for p in projects]
    current = st.session_state.get("project", names[0])
    index = names.index(current) if current in names else 0
    if st.session_state.get("_nav_project_locked"):
        selected = names[index]
        st.session_state["project"] = selected
        return selected
    selected = st.sidebar.selectbox("当前项目", names, index=index)
    st.session_state["project"] = selected
    return selected
