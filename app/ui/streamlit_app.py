import streamlit as st

from app.ui.layout import inject_css, render_dashboard, render_selected_page, render_sidebar
from app.ui.services import bootstrap


st.set_page_config(page_title="长篇记忆小说", page_icon="SM", layout="wide")

try:
    bootstrap()
    inject_css()
    project, section, page = render_sidebar()

    if st.sidebar.button("返回首页", use_container_width=True):
        st.session_state["show_dashboard"] = True

    if not st.session_state.get("_dashboard_seen"):
        st.session_state["_dashboard_seen"] = True
        render_dashboard(project)
    elif st.session_state.pop("show_dashboard", False):
        render_dashboard(project)
    else:
        render_selected_page(project, section, page)
except Exception as exc:
    st.error("页面启动失败。请查看 exe 同级目录的 start_log.txt，或检查 data/.env 配置。")
    st.exception(exc)
