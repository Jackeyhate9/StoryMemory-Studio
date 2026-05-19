import pandas as pd
import streamlit as st

from app.ui.components.project_selector import project_selector
from app.ui.services import foreshadow_options, run_payoff_plan, run_payoff_recommend


st.title("伏笔回收推荐")
project = project_selector()
if not project:
    st.stop()

st.info("系统会根据伏笔状态、首次出现章节、最近提及章节和当前剧情进度，推荐优先回收窗口。")

if st.button("推荐需要回收的伏笔", type="primary"):
    with st.spinner("正在计算伏笔遗忘风险和回收优先级..."):
        st.session_state["payoff_report"] = run_payoff_recommend(project)

report = st.session_state.get("payoff_report")
if report:
    recommendations = report.get("recommendations", [])
    if recommendations:
        st.dataframe(pd.DataFrame(recommendations), use_container_width=True, hide_index=True)
    with st.expander("完整推荐 JSON"):
        st.json(report)

foreshadows = foreshadow_options(project)
if foreshadows:
    labels = [f"{f['id']} - {f['name']} [{f['status']}]" for f in foreshadows]
    selected = st.selectbox("选择伏笔生成回收方案", labels)
    foreshadow_id = int(selected.split(" - ")[0])
    if st.button("生成伏笔回收章节方案"):
        with st.spinner("正在生成方案..."):
            plan = run_payoff_plan(project, foreshadow_id)
        st.text_area("回收方案", plan["plan"], height=260)
else:
    st.caption("当前项目还没有伏笔。可以先导入章节并抽取记忆。")
