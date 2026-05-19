import streamlit as st

from app.ui.components.memory_cards import show_table
from app.ui.components.project_selector import project_selector
from app.ui.services import memory_dashboard


st.title("记忆库看板")
project = project_selector()
if not project:
    st.stop()

st.info("这里展示 AI 写作时会优先参考的长期记忆。可以搜索人物、地点、道具、伏笔、规则或章节事实。")

search = st.text_input("搜索记忆", placeholder="输入人物名、地点、道具、伏笔、关键词")
data = memory_dashboard(project, search)

metric_cols = st.columns(6)
metric_cols[0].metric("人物", len(data["characters"]))
metric_cols[1].metric("世界观", len(data["world_rules"]))
metric_cols[2].metric("伏笔", len(data["foreshadows"]))
metric_cols[3].metric("时间线", len(data["timeline_events"]))
metric_cols[4].metric("未解决问题", len(data["unresolved_questions"]))
metric_cols[5].metric("章节事实", len(data["chapter_facts"]))

tabs = st.tabs(["人物卡", "关系/势力", "世界观/能力", "伏笔", "时间线", "摘要/事实", "未解决问题"])
with tabs[0]:
    show_table("人物卡", data["characters"], ["id", "name", "role", "personality", "motivation", "status", "current_location", "hard_constraints"])
with tabs[1]:
    show_table("人物关系", data["character_relationships"], ["id", "character_a_name", "character_b_name", "relationship_type", "status", "description"])
    show_table("势力组织", data["organizations"], ["id", "name", "type", "leader", "status", "description"])
with tabs[2]:
    show_table("世界观规则", data["world_rules"], ["id", "category", "rule_text", "rigidity", "source"])
    show_table("能力体系", data["abilities"], ["id", "name", "owner", "system", "description", "limitations"])
    show_table("道具", data["items"], ["id", "name", "type", "owner", "location", "status", "description"])
with tabs[3]:
    show_table("伏笔表", data["foreshadows"], ["id", "name", "status", "related_thread", "expected_resolution_chapter", "last_mentioned_chapter_id", "risk_note"])
with tabs[4]:
    show_table("时间线", data["timeline_events"], ["id", "story_time", "sort_key", "event_text", "location", "characters_json", "duration"])
with tabs[5]:
    show_table("章节摘要", data["chapter_summaries"], ["id", "chapter_id", "short_summary", "detailed_summary"])
    show_table("章节事实", data["chapter_facts"], ["id", "chapter_id", "fact_type", "subject", "fact_text", "source_quote"])
with tabs[6]:
    show_table("未解决问题", data["unresolved_questions"], ["id", "question", "related_thread", "status", "priority", "notes"])
