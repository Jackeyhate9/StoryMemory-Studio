import pandas as pd
import streamlit as st

from app.ui.components.project_selector import project_selector
from app.ui.services import (
    delete_memory_row,
    editable_fields,
    editable_table_labels,
    get_memory_row,
    list_memory_rows,
    upsert_memory_row,
)


MULTILINE_FIELDS = {
    "description",
    "rules",
    "hard_constraints",
    "personality",
    "motivation",
    "secrets",
    "abilities",
    "rule_text",
    "risk_note",
    "evidence",
    "notes",
    "event_text",
    "fact_text",
    "source_quote",
    "short_summary",
    "detailed_summary",
    "safe_style_summary",
    "profile_json",
    "do_rules_json",
    "dont_rules_json",
}
NUMBER_FIELDS = {"is_active", "is_default", "expected_resolution_chapter", "last_mentioned_chapter_id", "chapter_id", "importance"}
FLOAT_FIELDS = {"certainty", "confidence"}


def field_input(field: str, value=""):
    if field in NUMBER_FIELDS:
        return st.number_input(field, min_value=0, step=1, value=int(value or 0))
    if field in FLOAT_FIELDS:
        return st.number_input(field, min_value=0.0, max_value=1.0, step=0.05, value=float(value or 0))
    if field in MULTILINE_FIELDS:
        return st.text_area(field, value=str(value or ""), height=120)
    return st.text_input(field, value=str(value or ""))


st.title("记忆编辑器")
project = project_selector()
if not project:
    st.stop()

st.info("可以人工修正 AI 抽取出的长期记忆。保存、新增、删除都会写入 edit_logs，方便追踪。")

labels = editable_table_labels()
label_to_table = {label: table for table, label in labels.items()}
selected_label = st.selectbox("记忆类型", list(label_to_table.keys()))
table = label_to_table[selected_label]
fields = editable_fields(table)

search = st.text_input("搜索", placeholder="输入关键词筛选当前记忆类型")
rows = list_memory_rows(project, table, search)
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

mode = st.radio("操作", ["新增", "编辑", "删除"], horizontal=True)

if mode == "新增":
    with st.form("add_memory"):
        st.subheader(f"新增{selected_label}")
        payload = {field: field_input(field) for field in fields}
        if st.form_submit_button("保存新增", type="primary"):
            try:
                row_id = upsert_memory_row(project, table, payload)
                st.success(f"已新增，ID：{row_id}")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

elif mode == "编辑":
    if not rows:
        st.caption("暂无可编辑记录。")
    else:
        row_ids = [int(row["id"]) for row in rows]
        row_id = st.selectbox("选择记录 ID", row_ids)
        row = get_memory_row(project, table, int(row_id)) or {}
        with st.form("edit_memory"):
            st.subheader(f"编辑{selected_label} #{row_id}")
            payload = {field: field_input(field, row.get(field, "")) for field in fields}
            if st.form_submit_button("保存修改", type="primary"):
                try:
                    upsert_memory_row(project, table, payload, int(row_id))
                    st.success("修改已保存。")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

else:
    if not rows:
        st.caption("暂无可删除记录。")
    else:
        row_ids = [int(row["id"]) for row in rows]
        row_id = st.selectbox("选择要删除的记录 ID", row_ids)
        confirm = st.checkbox("我确认删除这条记忆")
        if st.button("确认删除", type="primary", disabled=not confirm):
            delete_memory_row(project, table, int(row_id))
            st.success("已删除。")
            st.rerun()
