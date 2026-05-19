import streamlit as st

from app.ui.sections._legacy import render_legacy


def render(project=None):
    st.session_state["adaptation_default_type"] = "poster"
    render_legacy("15_adaptation_matrix.py", project)
