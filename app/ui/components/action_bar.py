from __future__ import annotations

import streamlit as st


def action_bar(run_label: str = "运行", save_label: str = "保存", export_label: str = "导出") -> tuple[bool, bool, bool]:
    cols = st.columns(3)
    run = cols[0].button(run_label, type="primary", use_container_width=True)
    save = cols[1].button(save_label, use_container_width=True)
    export = cols[2].button(export_label, use_container_width=True)
    return run, save, export
