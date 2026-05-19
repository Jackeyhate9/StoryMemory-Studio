import json
from collections import defaultdict

import pandas as pd
import streamlit as st

from app.ui.components.project_selector import project_selector
from app.ui.services import delete_timeline_event, timeline_events, upsert_timeline_event


st.title("时间线管理")
project = project_selector()
if not project:
    st.stop()

st.info("时间线用于检查同一角色同一时间出现在多个地点、旅程耗时不合理、伤势恢复过快等问题。")

order = st.radio("排序方式", ["chapter", "story_time"], format_func=lambda x: "按章节" if x == "chapter" else "按故事内时间", horizontal=True)
rows = timeline_events(project, order)
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.subheader("新增或编辑时间线事件")
mode = st.radio("操作", ["新增", "编辑", "删除"], horizontal=True)
selected = None
if rows and mode in {"编辑", "删除"}:
    ids = [int(row["id"]) for row in rows]
    selected_id = st.selectbox("选择事件 ID", ids)
    selected = next(row for row in rows if int(row["id"]) == int(selected_id))

if mode in {"新增", "编辑"}:
    with st.form("timeline_form"):
        chapter_id = st.number_input("关联章节 ID（可为 0）", min_value=0, step=1, value=int((selected or {}).get("chapter_id") or 0))
        c1, c2 = st.columns(2)
        with c1:
            story_time = st.text_input("故事内时间", value=(selected or {}).get("story_time", ""))
            sort_key = st.text_input("排序键", value=(selected or {}).get("sort_key", ""))
            location = st.text_input("地点", value=(selected or {}).get("location", ""))
        with c2:
            characters_json = st.text_input("出场角色 JSON", value=(selected or {}).get("characters_json", "[]"))
            duration = st.text_input("持续时间", value=(selected or {}).get("duration", ""))
            confidence = st.number_input("可信度", min_value=0.0, max_value=1.0, step=0.05, value=float((selected or {}).get("confidence") or 1.0))
        event_text = st.text_area("事件内容", value=(selected or {}).get("event_text", ""), height=120)
        if st.form_submit_button("保存时间线事件", type="primary"):
            try:
                json.loads(characters_json or "[]")
                row_id = upsert_timeline_event(
                    project,
                    {
                        "chapter_id": chapter_id,
                        "story_time": story_time,
                        "sort_key": sort_key,
                        "event_text": event_text,
                        "location": location,
                        "characters_json": characters_json,
                        "duration": duration,
                        "confidence": confidence,
                    },
                    int(selected["id"]) if selected else None,
                )
                st.success(f"已保存时间线事件：{row_id}")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
elif mode == "删除" and selected:
    st.warning("删除时间线事件会写入编辑日志。")
    confirm = st.checkbox("确认删除该时间线事件")
    if st.button("删除事件", type="primary", disabled=not confirm):
        delete_timeline_event(project, int(selected["id"]))
        st.success("已删除。")
        st.rerun()

st.subheader("冲突检查")
if st.button("检查角色同一时间多地点冲突", type="primary"):
    by_key = defaultdict(list)
    for row in rows:
        try:
            chars = json.loads(row.get("characters_json") or "[]")
        except json.JSONDecodeError:
            chars = []
        for char in chars:
            by_key[(row.get("story_time"), char)].append(row)
    conflicts = []
    for (story_time, char), items in by_key.items():
        locations = {x.get("location") for x in items if x.get("location")}
        if story_time and len(locations) > 1:
            conflicts.append({"story_time": story_time, "character": char, "locations": sorted(locations), "events": items})
    if conflicts:
        st.error("发现时间线冲突。")
        st.json(conflicts)
    else:
        st.success("未发现同一时间多地点冲突。")
