from __future__ import annotations

import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def render_legacy(filename: str, project: str | None = None) -> None:
    if project:
        import streamlit as st

        st.session_state["project"] = project
        st.session_state["_nav_project_locked"] = True
    runpy.run_path(str(ROOT / "legacy_pages" / filename), run_name=f"storymemory_{filename}")
