import pandas as pd
import streamlit as st

from app.ui.components.project_selector import project_selector
from app.ui.services import memory_dashboard, update_foreshadow

st.title("伏笔管理")
project = project_selector()
if not project:
    st.stop()

st.info("伏笔管理用于防止埋了不回收、已回收又重复当作悬念、或回收章节过晚。")

rows = memory_dashboard(project)["foreshadows"]
status_filter = st.multiselect("状态筛选", ["unresolved", "partial", "resolved", "abandoned", "未回收", "部分回收", "已回收"], default=[])
if status_filter:
    rows = [r for r in rows if r.get("status") in status_filter]
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

if rows:
    ids = [int(r["id"]) for r in rows]
    row_id = st.selectbox("选择伏笔 ID", ids)
    current = next(r for r in rows if int(r["id"]) == row_id)
    statuses = ["unresolved", "partial", "resolved", "abandoned"]
    current_status = current.get("status") if current.get("status") in statuses else "unresolved"
    status = st.selectbox("状态", statuses, index=statuses.index(current_status))
    expected = st.number_input("预计回收章节", min_value=0, value=int(current.get("expected_resolution_chapter") or 0), step=1)
    resolution = st.text_area("回收方式", current.get("resolution_method") or "")
    risk = st.text_area("风险提示", current.get("risk_note") or "")
    if st.button("更新伏笔", type="primary"):
        update_foreshadow(project, row_id, status, int(expected) if expected else None, resolution, risk)
        st.success("伏笔已更新。")
        st.rerun()
else:
    st.caption("暂无伏笔。导入更多章节或使用模型抽取后会逐步出现。")

