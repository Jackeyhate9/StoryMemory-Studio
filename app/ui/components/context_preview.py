import streamlit as st


def context_preview(text: str) -> None:
    st.subheader("上下文预览")
    st.text_area("即将发送给模型的结构化上下文", text, height=420)
    st.caption(f"约 {max(1, len(text) // 2):,} tokens（粗略估算）")
