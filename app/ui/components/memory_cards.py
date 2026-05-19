import pandas as pd
import streamlit as st


def show_table(title: str, rows: list[dict], columns: list[str] | None = None) -> None:
    st.subheader(title)
    if not rows:
        st.caption("暂无数据")
        return
    df = pd.DataFrame(rows)
    if columns:
        available = [c for c in columns if c in df.columns]
        df = df[available]
    st.dataframe(df, use_container_width=True, hide_index=True)

