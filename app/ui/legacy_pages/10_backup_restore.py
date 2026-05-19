from pathlib import Path

import pandas as pd
import streamlit as st

from app.db.database import db_session, get_project
from app.export.bible_export import export_bible
from app.export.json_export import export_project_json
from app.ui.components.project_selector import project_selector
from app.ui.services import create_backup, health_snapshot, list_backups, restore_backup


st.title("备份与恢复")
project = project_selector()

st.info("本页用于保护本地数据。建议在批量导入、记忆编辑、恢复备份前先创建备份。")

health = health_snapshot()
st.markdown(
    f"""
    - 当前数据库：`{health["database_path"]}`
    - 数据目录：`{health["data_dir"]}`
    - 备份内容：本地 SQLite 数据库、配置文件、data 目录下的结构化导出文件
    """
)

st.subheader("创建备份")
note = st.text_input("备份备注", placeholder="例如 before_big_import")
if st.button("立即创建备份", type="primary"):
    try:
        path = create_backup(note)
        st.success(f"备份已创建：{path}")
    except Exception as exc:
        st.error(str(exc))

st.subheader("导出设定包")
if project:
    export_dir = st.text_input("导出目录", value=str(Path("exports") / project))
    c1, c2 = st.columns(2)
    if c1.button("导出小说设定包", use_container_width=True):
        try:
            with db_session() as conn:
                p = get_project(conn, project)
                path = export_bible(conn, p["id"], Path(export_dir))
            st.success(f"已导出：{path}")
        except Exception as exc:
            st.error(str(exc))
    if c2.button("导出 story_memory.json", use_container_width=True):
        try:
            with db_session() as conn:
                p = get_project(conn, project)
                path = export_project_json(conn, p["id"], Path(export_dir) / "story_memory.json")
            st.success(f"已导出：{path}")
        except Exception as exc:
            st.error(str(exc))
else:
    st.caption("选择项目后可导出 world_bible、character_bible、outline、timeline、foreshadows 和 story_memory.json。")

st.subheader("已有备份")
backups = list_backups()
if backups:
    st.dataframe(pd.DataFrame(backups), use_container_width=True, hide_index=True)
    selected = st.selectbox("下载备份", [row["path"] for row in backups])
    selected_path = Path(selected)
    if selected_path.exists():
        st.download_button("下载选中备份", selected_path.read_bytes(), file_name=selected_path.name, mime="application/zip")
else:
    st.caption("暂无备份。")

st.subheader("从备份恢复")
uploaded = st.file_uploader("上传长篇记忆小说备份包", type=["zip"])
st.warning("恢复会覆盖当前数据库。系统会先自动创建一份恢复前备份。")
confirm = st.checkbox("我确认要恢复上传的备份")
if st.button("恢复备份", disabled=not uploaded or not confirm):
    try:
        before = restore_backup(uploaded.getvalue())
        st.success(f"恢复完成。恢复前备份已保存：{before}")
        st.rerun()
    except Exception as exc:
        st.error(str(exc))
